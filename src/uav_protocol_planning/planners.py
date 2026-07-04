from __future__ import annotations

import random
from typing import Iterable, List, Set, Tuple

from .geometry import distance_m
from .metrics import route_temporal_metrics
from .models import Scenario
from .simulation import advance_state, estimate_visit, initial_state, simulate_route


def distance_only_route(scenario: Scenario) -> Tuple[str, ...]:
    remaining: Set[str] = set(scenario.nodes)
    current_point = scenario.start
    route: List[str] = []

    while remaining:
        next_id = min(
            remaining,
            key=lambda node_id: distance_m(current_point, scenario.nodes[node_id].point),
        )
        route.append(next_id)
        current_point = scenario.nodes[next_id].point
        remaining.remove(next_id)

    return tuple(route)


def ordinary_data_collection_route(scenario: Scenario) -> Tuple[str, ...]:
    remaining: Set[str] = set(scenario.nodes)
    current_point = scenario.start
    route: List[str] = []

    while remaining:
        next_id = min(
            remaining,
            key=lambda node_id: _ordinary_visit_cost(scenario, current_point, node_id),
        )
        route.append(next_id)
        current_point = scenario.nodes[next_id].point
        remaining.remove(next_id)

    seeds = {tuple(route), distance_only_route(scenario)}
    searched = [_ordinary_local_search_route(scenario, seed) for seed in seeds]
    return min(searched, key=lambda candidate: _ordinary_route_objective(scenario, candidate))


def protocol_aware_route(
    scenario: Scenario,
    blackout_weight: float = 3.0,
    radio_obstacle_penalty_s: float = 20.0,
    priority_weight_s: float = 3.0,
    max_passes: int = 30,
) -> Tuple[str, ...]:
    greedy_seed = _protocol_aware_greedy_seed(
        scenario=scenario,
        blackout_weight=blackout_weight,
        radio_obstacle_penalty_s=radio_obstacle_penalty_s,
        priority_weight_s=priority_weight_s,
    )
    balanced_seed = _protocol_aware_greedy_seed(
        scenario=scenario,
        blackout_weight=3.0,
        radio_obstacle_penalty_s=radio_obstacle_penalty_s,
        priority_weight_s=priority_weight_s,
    )
    distance_seed = distance_only_route(scenario)

    seeds = {greedy_seed, balanced_seed, distance_seed}
    if blackout_weight != 3.0:
        balanced_routes = {
            _local_search_route(scenario, seed, blackout_weight=3.0, max_passes=max_passes)
            for seed in seeds
        }
        seeds.update(balanced_routes)

    searched = [
        _local_search_route(scenario, seed, blackout_weight, max_passes=max_passes)
        for seed in seeds
    ]
    return min(searched, key=lambda route: _route_objective(scenario, route, blackout_weight))


def soft_blackout_penalty_route(
    scenario: Scenario,
    blackout_weight: float = 12.0,
    budget: float | None = None,
) -> Tuple[str, ...]:
    """Protocol-aware route with a fixed soft penalty on blackout overruns."""
    if budget is None:
        return protocol_aware_route(scenario, blackout_weight=blackout_weight)

    from dataclasses import replace

    scored_scenario = replace(scenario, max_blackout_s=budget)
    return protocol_aware_route(scored_scenario, blackout_weight=blackout_weight)


def average_gap_route(
    scenario: Scenario,
    max_passes: int = 24,
) -> Tuple[str, ...]:
    """Baseline that minimizes the mean no-data gap rather than the worst gap."""
    seeds = _metric_baseline_seeds(scenario)
    candidates = {
        _custom_local_search_route(
            scenario,
            seed,
            _average_gap_objective,
            max_passes=max_passes,
        )
        for seed in seeds
    }
    candidates.update(seeds)
    return min(candidates, key=lambda route: _average_gap_objective(scenario, route))


def freshness_focused_route(
    scenario: Scenario,
    max_passes: int = 24,
) -> Tuple[str, ...]:
    """AoI-like baseline that minimizes mean node collection completion time."""
    seeds = _metric_baseline_seeds(scenario)
    candidates = {
        _custom_local_search_route(
            scenario,
            seed,
            _freshness_objective,
            max_passes=max_passes,
        )
        for seed in seeds
    }
    candidates.update(seeds)
    return min(candidates, key=lambda route: _freshness_objective(scenario, route))


def genetic_algorithm_route(
    scenario: Scenario,
    blackout_weight: float = 3.0,
    population_size: int = 32,
    generations: int = 70,
    mutation_rate: float = 0.18,
    seed: int = 17,
) -> Tuple[str, ...]:
    rng = random.Random(seed)
    node_ids = tuple(scenario.nodes)
    seeds = [
        distance_only_route(scenario),
        _protocol_aware_greedy_seed(
            scenario=scenario,
            blackout_weight=blackout_weight,
            radio_obstacle_penalty_s=20.0,
            priority_weight_s=3.0,
        ),
        protocol_aware_route(scenario, blackout_weight=blackout_weight),
    ]

    population: List[Tuple[str, ...]] = list(dict.fromkeys(seeds))
    while len(population) < population_size:
        candidate = list(node_ids)
        rng.shuffle(candidate)
        population.append(tuple(candidate))

    best = min(population, key=lambda route: _route_objective(scenario, route, blackout_weight))

    for _ in range(generations):
        ranked = sorted(population, key=lambda route: _route_objective(scenario, route, blackout_weight))
        next_population = ranked[: max(2, population_size // 5)]
        best = ranked[0] if _route_objective(scenario, ranked[0], blackout_weight) < _route_objective(scenario, best, blackout_weight) else best

        while len(next_population) < population_size:
            parent_a = _tournament_select(rng, population, scenario, blackout_weight)
            parent_b = _tournament_select(rng, population, scenario, blackout_weight)
            child = _ordered_crossover(rng, parent_a, parent_b)
            if rng.random() < mutation_rate:
                child = _mutate_swap(rng, child)
            next_population.append(child)

        population = next_population

    best = min(population + [best], key=lambda route: _route_objective(scenario, route, blackout_weight))
    return _local_search_route(scenario, best, blackout_weight, max_passes=18)


def particle_swarm_route(
    scenario: Scenario,
    blackout_weight: float = 3.0,
    swarm_size: int = 28,
    iterations: int = 80,
    seed: int = 23,
) -> Tuple[str, ...]:
    rng = random.Random(seed)
    node_ids = tuple(scenario.nodes)
    dimension = len(node_ids)
    inertia = 0.68
    cognitive = 1.35
    social = 1.35

    seed_routes = [
        distance_only_route(scenario),
        ordinary_data_collection_route(scenario),
        protocol_aware_route(scenario, blackout_weight=blackout_weight),
    ]
    positions = [_position_from_route(route, node_ids) for route in seed_routes]
    velocities = [[0.0] * dimension for _ in positions]

    while len(positions) < swarm_size:
        positions.append([rng.random() for _ in range(dimension)])
        velocities.append([rng.uniform(-0.12, 0.12) for _ in range(dimension)])

    personal_best = [position[:] for position in positions]
    personal_scores = [
        _route_objective(scenario, _route_from_position(position, node_ids), blackout_weight)
        for position in positions
    ]
    best_index = min(range(len(personal_best)), key=lambda index: personal_scores[index])
    global_best = personal_best[best_index][:]
    global_score = personal_scores[best_index]

    for _ in range(iterations):
        for index, position in enumerate(positions):
            velocity = velocities[index]
            for axis in range(dimension):
                velocity[axis] = (
                    inertia * velocity[axis]
                    + cognitive * rng.random() * (personal_best[index][axis] - position[axis])
                    + social * rng.random() * (global_best[axis] - position[axis])
                )
                velocity[axis] = max(-0.45, min(0.45, velocity[axis]))
                position[axis] += velocity[axis]

            route = _route_from_position(position, node_ids)
            score = _route_objective(scenario, route, blackout_weight)
            if score < personal_scores[index]:
                personal_scores[index] = score
                personal_best[index] = position[:]
                if score < global_score:
                    global_score = score
                    global_best = position[:]

    best_route = _route_from_position(global_best, node_ids)
    return _local_search_route(scenario, best_route, blackout_weight, max_passes=16)


def genetic_algorithm_blackout_route(
    scenario: Scenario,
    population_size: int = 32,
    generations: int = 70,
    mutation_rate: float = 0.18,
    seed: int = 31,
) -> Tuple[str, ...]:
    """GA baseline that directly minimizes maximum blackout, breaking ties by time."""
    rng = random.Random(seed)
    node_ids = tuple(scenario.nodes)
    seeds = [
        distance_only_route(scenario),
        ordinary_data_collection_route(scenario),
        protocol_aware_route(scenario, blackout_weight=0.0),
        protocol_aware_route(scenario, blackout_weight=12.0),
    ]

    population: List[Tuple[str, ...]] = list(dict.fromkeys(seeds))
    while len(population) < population_size:
        candidate = list(node_ids)
        rng.shuffle(candidate)
        population.append(tuple(candidate))

    best = min(population, key=lambda route: _blackout_route_objective(scenario, route))

    for _ in range(generations):
        ranked = sorted(population, key=lambda route: _blackout_route_objective(scenario, route))
        next_population = ranked[: max(2, population_size // 5)]
        if _blackout_route_objective(scenario, ranked[0]) < _blackout_route_objective(scenario, best):
            best = ranked[0]

        while len(next_population) < population_size:
            parent_a = _tournament_select_custom(
                rng,
                population,
                lambda route: _blackout_route_objective(scenario, route),
            )
            parent_b = _tournament_select_custom(
                rng,
                population,
                lambda route: _blackout_route_objective(scenario, route),
            )
            child = _ordered_crossover(rng, parent_a, parent_b)
            if rng.random() < mutation_rate:
                child = _mutate_swap(rng, child)
            next_population.append(child)

        population = next_population

    best = min(population + [best], key=lambda route: _blackout_route_objective(scenario, route))
    return _custom_local_search_route(
        scenario,
        best,
        _blackout_route_objective,
        max_passes=18,
    )


def particle_swarm_blackout_route(
    scenario: Scenario,
    swarm_size: int = 28,
    iterations: int = 80,
    seed: int = 37,
) -> Tuple[str, ...]:
    """PSO baseline that directly minimizes maximum blackout, breaking ties by time."""
    rng = random.Random(seed)
    node_ids = tuple(scenario.nodes)
    dimension = len(node_ids)
    inertia = 0.68
    cognitive = 1.35
    social = 1.35

    seed_routes = [
        distance_only_route(scenario),
        ordinary_data_collection_route(scenario),
        protocol_aware_route(scenario, blackout_weight=0.0),
        protocol_aware_route(scenario, blackout_weight=12.0),
    ]
    positions = [_position_from_route(route, node_ids) for route in seed_routes]
    velocities = [[0.0] * dimension for _ in positions]

    while len(positions) < swarm_size:
        positions.append([rng.random() for _ in range(dimension)])
        velocities.append([rng.uniform(-0.12, 0.12) for _ in range(dimension)])

    personal_best = [position[:] for position in positions]
    personal_scores = [
        _blackout_route_objective(scenario, _route_from_position(position, node_ids))
        for position in positions
    ]
    best_index = min(range(len(personal_best)), key=lambda index: personal_scores[index])
    global_best = personal_best[best_index][:]
    global_score = personal_scores[best_index]

    for _ in range(iterations):
        for index, position in enumerate(positions):
            velocity = velocities[index]
            for axis in range(dimension):
                velocity[axis] = (
                    inertia * velocity[axis]
                    + cognitive * rng.random() * (personal_best[index][axis] - position[axis])
                    + social * rng.random() * (global_best[axis] - position[axis])
                )
                velocity[axis] = max(-0.45, min(0.45, velocity[axis]))
                position[axis] += velocity[axis]

            route = _route_from_position(position, node_ids)
            score = _blackout_route_objective(scenario, route)
            if score < personal_scores[index]:
                personal_scores[index] = score
                personal_best[index] = position[:]
                if score < global_score:
                    global_score = score
                    global_best = position[:]

    best_route = _route_from_position(global_best, node_ids)
    return _custom_local_search_route(
        scenario,
        best_route,
        _blackout_route_objective,
        max_passes=16,
    )


def q_learning_blackout_route(
    scenario: Scenario,
    budget: float = 90.0,
    episodes: int = 360,
    alpha: float = 0.24,
    discount: float = 0.88,
    epsilon_start: float = 0.45,
    epsilon_end: float = 0.05,
    seed: int = 41,
) -> Tuple[str, ...]:
    """Learning-style baseline for route ordering.

    The learner treats the next unvisited node as the action and uses the same
    route evaluator as the other planners. It is intentionally lightweight and
    reproducible; the paper uses it as a learning-family comparator rather than
    as a claim about a specific deep-RL architecture.
    """
    rng = random.Random(seed)
    node_ids = tuple(scenario.nodes)
    all_mask = (1 << len(node_ids)) - 1
    q_values: dict[tuple[int, int, int, int], dict[int, float]] = {}

    def key(mask: int, current_index: int, state) -> tuple[int, int, int, int]:
        time_bin = min(20, int(state.current_time_s // 180.0))
        gap_bin = min(20, int((state.current_time_s - state.last_comm_time_s) // 30.0))
        return (mask, current_index, time_bin, gap_bin)

    def score_step(estimate, next_state, done: bool) -> float:
        budget_excess_s = max(0.0, estimate.communication_gap_s - budget)
        step_cost = (
            estimate.total_s
            + 0.10 * estimate.communication_gap_s
            + 7.0 * budget_excess_s
        )
        if done:
            return_gap_s = (
                distance_m(next_state.current_point, scenario.start) / scenario.speed_mps
            )
            step_cost += 2.0 * max(0.0, return_gap_s - budget)
        return -step_cost

    for episode in range(max(1, episodes)):
        state = initial_state(scenario)
        mask = 0
        current_index = -1
        decay = episode / max(1, episodes - 1)
        epsilon = epsilon_start + (epsilon_end - epsilon_start) * decay

        while mask != all_mask:
            valid = [
                index
                for index in range(len(node_ids))
                if not (mask & (1 << index))
            ]
            state_key = key(mask, current_index, state)
            q_values.setdefault(state_key, {})

            if rng.random() < epsilon:
                action_index = rng.choice(valid)
            else:
                action_index = max(
                    valid,
                    key=lambda index: (
                        q_values[state_key].get(index, 0.0),
                        -index,
                    ),
                )

            node = scenario.nodes[node_ids[action_index]]
            next_state, estimate = advance_state(scenario, state, node)
            next_mask = mask | (1 << action_index)
            done = next_mask == all_mask
            reward = score_step(estimate, next_state, done)

            next_key = key(next_mask, action_index, next_state)
            next_valid = [
                index
                for index in range(len(node_ids))
                if not (next_mask & (1 << index))
            ]
            next_value = 0.0
            if next_valid:
                q_values.setdefault(next_key, {})
                next_value = max(q_values[next_key].get(index, 0.0) for index in next_valid)

            old_value = q_values[state_key].get(action_index, 0.0)
            q_values[state_key][action_index] = old_value + alpha * (
                reward + discount * next_value - old_value
            )

            state = next_state
            mask = next_mask
            current_index = action_index

    route = _q_learning_greedy_route(scenario, node_ids, q_values, budget)
    candidates = {
        route,
        _custom_local_search_route(
            scenario,
            route,
            _blackout_route_objective,
            max_passes=8,
        ),
    }
    return min(candidates, key=lambda candidate: _blackout_route_objective(scenario, candidate))


def neural_q_blackout_route(
    scenario: Scenario,
    budget: float = 90.0,
    episodes: int = 220,
    hidden_size: int = 24,
    learning_rate: float = 0.004,
    discount: float = 0.88,
    epsilon_start: float = 0.45,
    epsilon_end: float = 0.06,
    replay_capacity: int = 5000,
    batch_size: int = 16,
    seed: int = 53,
) -> Tuple[str, ...]:
    """DQN-style learning comparator using a small neural action-value model.

    This keeps the same next-node action space and route evaluator as the
    tabular Q-learning comparator, but replaces the lookup table with a compact
    neural value approximator trained with replay and a target network.
    """
    import numpy as np

    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    node_ids = tuple(scenario.nodes)
    protocol_ids = tuple(sorted(scenario.protocols))
    protocol_index = {name: index for index, name in enumerate(protocol_ids)}
    all_mask = (1 << len(node_ids)) - 1
    input_dim = 17 + len(protocol_ids)

    weights = {
        "w1": np_rng.normal(0.0, 0.10, size=(input_dim, hidden_size)),
        "b1": np.zeros(hidden_size),
        "w2": np_rng.normal(0.0, 0.08, size=(hidden_size, 1)),
        "b2": np.zeros(1),
    }
    target_weights = {key: value.copy() for key, value in weights.items()}
    replay: list[tuple[object, float, int, int, object, bool]] = []

    def features(mask: int, state, action_index: int) -> np.ndarray:
        node = scenario.nodes[node_ids[action_index]]
        estimate = estimate_visit(scenario, state, node)
        current_gap_s = state.current_time_s - state.last_comm_time_s
        remaining_count = len(node_ids) - int(mask.bit_count())
        values = [
            int(mask.bit_count()) / max(1, len(node_ids)),
            remaining_count / max(1, len(node_ids)),
            state.current_time_s / 3000.0,
            current_gap_s / max(1.0, budget),
            state.current_point[0] / max(1.0, scenario.width_m),
            state.current_point[1] / max(1.0, scenario.height_m),
            node.x_m / max(1.0, scenario.width_m),
            node.y_m / max(1.0, scenario.height_m),
            estimate.travel_s / 800.0,
            estimate.wait_s / 300.0,
            estimate.setup_s / 40.0,
            estimate.switch_s / 20.0,
            estimate.transfer_s / 300.0,
            estimate.communication_gap_s / max(1.0, budget),
            max(0.0, estimate.communication_gap_s - budget) / max(1.0, budget),
            node.data_kb / 1200.0,
            node.priority / 10.0,
        ]
        one_hot = [0.0] * len(protocol_ids)
        one_hot[protocol_index[node.protocol]] = 1.0
        return np.asarray(values + one_hot, dtype=float)

    def forward(batch: np.ndarray, params) -> tuple[np.ndarray, np.ndarray]:
        hidden = np.maximum(0.0, batch @ params["w1"] + params["b1"])
        q_values = hidden @ params["w2"] + params["b2"]
        return q_values.reshape(-1), hidden

    def reward_for_step(estimate, next_state, done: bool) -> float:
        budget_excess_s = max(0.0, estimate.communication_gap_s - budget)
        cost = estimate.total_s + 0.10 * estimate.communication_gap_s + 7.0 * budget_excess_s
        if done:
            return_gap_s = distance_m(next_state.current_point, scenario.start) / scenario.speed_mps
            cost += 2.0 * max(0.0, return_gap_s - budget)
        return -cost / 200.0

    def max_next_value(next_mask: int, action_index: int, next_state) -> float:
        if next_mask == all_mask:
            return 0.0
        valid = [
            index
            for index in range(len(node_ids))
            if not (next_mask & (1 << index))
        ]
        batch = np.vstack([features(next_mask, next_state, index) for index in valid])
        q_values, _ = forward(batch, target_weights)
        return float(np.max(q_values))

    def train_step() -> None:
        if len(replay) < batch_size:
            return
        sample = rng.sample(replay, batch_size)
        x_batch = np.vstack([item[0] for item in sample])
        targets = []
        for _, reward, next_mask, action_index, next_state, done in sample:
            targets.append(reward if done else reward + discount * max_next_value(next_mask, action_index, next_state))
        y = np.asarray(targets, dtype=float)

        predictions, hidden = forward(x_batch, weights)
        error = predictions - y
        grad_output = (2.0 / len(sample)) * error.reshape(-1, 1)
        grad_w2 = hidden.T @ grad_output
        grad_b2 = grad_output.sum(axis=0)
        grad_hidden = grad_output @ weights["w2"].T
        grad_hidden[hidden <= 0.0] = 0.0
        grad_w1 = x_batch.T @ grad_hidden
        grad_b1 = grad_hidden.sum(axis=0)

        for gradient in (grad_w1, grad_b1, grad_w2, grad_b2):
            np.clip(gradient, -5.0, 5.0, out=gradient)
        weights["w1"] -= learning_rate * grad_w1
        weights["b1"] -= learning_rate * grad_b1
        weights["w2"] -= learning_rate * grad_w2
        weights["b2"] -= learning_rate * grad_b2

    for episode in range(max(1, episodes)):
        state = initial_state(scenario)
        mask = 0
        decay = episode / max(1, episodes - 1)
        epsilon = epsilon_start + (epsilon_end - epsilon_start) * decay

        while mask != all_mask:
            valid = [
                index
                for index in range(len(node_ids))
                if not (mask & (1 << index))
            ]
            if rng.random() < epsilon:
                action_index = rng.choice(valid)
            else:
                batch = np.vstack([features(mask, state, index) for index in valid])
                q_values, _ = forward(batch, weights)
                action_index = valid[int(np.argmax(q_values))]

            node = scenario.nodes[node_ids[action_index]]
            x = features(mask, state, action_index)
            next_state, estimate = advance_state(scenario, state, node)
            next_mask = mask | (1 << action_index)
            done = next_mask == all_mask
            replay.append((x, reward_for_step(estimate, next_state, done), next_mask, action_index, next_state, done))
            if len(replay) > replay_capacity:
                replay.pop(0)
            train_step()

            state = next_state
            mask = next_mask

        if episode % 20 == 0:
            target_weights = {key: value.copy() for key, value in weights.items()}

    target_weights = {key: value.copy() for key, value in weights.items()}
    route = _neural_q_greedy_route(scenario, node_ids, weights, features, forward)
    candidates = {
        route,
        _custom_local_search_route(
            scenario,
            route,
            _blackout_route_objective,
            max_passes=12,
        ),
    }
    return min(candidates, key=lambda candidate: _blackout_route_objective(scenario, candidate))


def _neural_q_greedy_route(
    scenario: Scenario,
    node_ids: Tuple[str, ...],
    weights,
    features,
    forward,
) -> Tuple[str, ...]:
    import numpy as np

    all_mask = (1 << len(node_ids)) - 1
    state = initial_state(scenario)
    mask = 0
    route: List[str] = []

    while mask != all_mask:
        valid = [
            index
            for index in range(len(node_ids))
            if not (mask & (1 << index))
        ]
        batch = np.vstack([features(mask, state, index) for index in valid])
        q_values, _ = forward(batch, weights)
        action_index = valid[int(np.argmax(q_values))]
        route.append(node_ids[action_index])
        state, _ = advance_state(scenario, state, scenario.nodes[node_ids[action_index]])
        mask |= 1 << action_index

    return tuple(route)


def _q_learning_greedy_route(
    scenario: Scenario,
    node_ids: Tuple[str, ...],
    q_values: dict[tuple[int, int, int, int], dict[int, float]],
    budget: float,
) -> Tuple[str, ...]:
    all_mask = (1 << len(node_ids)) - 1
    state = initial_state(scenario)
    mask = 0
    current_index = -1
    route: List[str] = []

    def key(mask_value: int, current_value: int, state_value) -> tuple[int, int, int, int]:
        time_bin = min(20, int(state_value.current_time_s // 180.0))
        gap_bin = min(20, int((state_value.current_time_s - state_value.last_comm_time_s) // 30.0))
        return (mask_value, current_value, time_bin, gap_bin)

    while mask != all_mask:
        valid = [
            index
            for index in range(len(node_ids))
            if not (mask & (1 << index))
        ]
        state_key = key(mask, current_index, state)

        def action_key(action_index: int) -> tuple[float, float, float, str]:
            node = scenario.nodes[node_ids[action_index]]
            estimate = estimate_visit(scenario, state, node)
            learned_value = q_values.get(state_key, {}).get(action_index, 0.0)
            gap_penalty = max(0.0, estimate.communication_gap_s - budget)
            return (
                -learned_value,
                gap_penalty,
                estimate.total_s,
                node_ids[action_index],
            )

        action_index = min(valid, key=action_key)
        route.append(node_ids[action_index])
        state, _ = advance_state(scenario, state, scenario.nodes[node_ids[action_index]])
        mask |= 1 << action_index
        current_index = action_index

    return tuple(route)


def _protocol_aware_greedy_seed(
    scenario: Scenario,
    blackout_weight: float,
    radio_obstacle_penalty_s: float,
    priority_weight_s: float,
) -> Tuple[str, ...]:
    remaining: Set[str] = set(scenario.nodes)
    route: List[str] = []
    state = initial_state(scenario)

    while remaining:
        scored = []
        for node_id in remaining:
            node = scenario.nodes[node_id]
            estimate = estimate_visit(scenario, state, node)
            blackout_overrun_s = max(0.0, estimate.communication_gap_s - scenario.max_blackout_s)
            score = (
                estimate.total_s
                + blackout_weight * blackout_overrun_s
                + radio_obstacle_penalty_s * estimate.radio_obstacle_hits
                - priority_weight_s * node.priority
            )
            scored.append((score, node_id, estimate))

        _, next_id, _ = min(scored, key=lambda item: (item[0], item[1]))
        route.append(next_id)
        state, _ = advance_state(scenario, state, scenario.nodes[next_id])
        remaining.remove(next_id)

    return tuple(route)


def _position_from_route(route: Tuple[str, ...], node_ids: Tuple[str, ...]) -> List[float]:
    rank = {node_id: index for index, node_id in enumerate(route)}
    scale = max(1, len(route) - 1)
    return [rank[node_id] / scale for node_id in node_ids]


def _route_from_position(position: List[float], node_ids: Tuple[str, ...]) -> Tuple[str, ...]:
    return tuple(
        node_id
        for _, node_id in sorted(zip(position, node_ids), key=lambda item: (item[0], item[1]))
    )


def _tournament_select(
    rng: random.Random,
    population: List[Tuple[str, ...]],
    scenario: Scenario,
    blackout_weight: float,
    tournament_size: int = 4,
) -> Tuple[str, ...]:
    competitors = rng.sample(population, k=min(tournament_size, len(population)))
    return min(competitors, key=lambda route: _route_objective(scenario, route, blackout_weight))


def _tournament_select_custom(
    rng: random.Random,
    population: List[Tuple[str, ...]],
    objective,
    tournament_size: int = 4,
) -> Tuple[str, ...]:
    competitors = rng.sample(population, k=min(tournament_size, len(population)))
    return min(competitors, key=objective)


def _ordered_crossover(
    rng: random.Random,
    parent_a: Tuple[str, ...],
    parent_b: Tuple[str, ...],
) -> Tuple[str, ...]:
    size = len(parent_a)
    left, right = sorted(rng.sample(range(size), 2))
    child: List[str | None] = [None] * size
    child[left:right] = parent_a[left:right]

    fill_values = [node_id for node_id in parent_b if node_id not in child]
    fill_index = 0
    for index, value in enumerate(child):
        if value is None:
            child[index] = fill_values[fill_index]
            fill_index += 1

    return tuple(node_id for node_id in child if node_id is not None)


def _mutate_swap(rng: random.Random, route: Tuple[str, ...]) -> Tuple[str, ...]:
    left, right = rng.sample(range(len(route)), 2)
    candidate = list(route)
    candidate[left], candidate[right] = candidate[right], candidate[left]
    return tuple(candidate)


def _route_objective(scenario: Scenario, route: Iterable[str], blackout_weight: float) -> float:
    result = simulate_route(scenario, route)
    blackout_overrun_s = max(0.0, result.max_blackout_s - scenario.max_blackout_s)
    return result.total_time_s + blackout_weight * blackout_overrun_s


def _blackout_route_objective(scenario: Scenario, route: Iterable[str]) -> Tuple[float, float]:
    result = simulate_route(scenario, route)
    return (
        round(result.max_blackout_s, 6),
        round(result.total_time_s, 6),
    )


def _ordinary_visit_cost(scenario: Scenario, current_point: Tuple[float, float], node_id: str) -> float:
    protocol_count = max(1, len(scenario.protocols))
    average_setup_s = sum(profile.connection_setup_s for profile in scenario.protocols.values()) / protocol_count
    average_rate_kb_s = (
        sum(profile.data_rate_kbps for profile in scenario.protocols.values()) / protocol_count
    ) / 8.0
    node = scenario.nodes[node_id]
    travel_s = distance_m(current_point, node.point) / scenario.speed_mps
    transfer_s = node.data_kb / max(0.01, average_rate_kb_s)
    return travel_s + average_setup_s + transfer_s


def _ordinary_route_objective(scenario: Scenario, route: Iterable[str]) -> float:
    route_tuple = tuple(route)
    current_point = scenario.start
    total_s = 0.0
    for node_id in route_tuple:
        total_s += _ordinary_visit_cost(scenario, current_point, node_id)
        current_point = scenario.nodes[node_id].point
    total_s += distance_m(current_point, scenario.start) / scenario.speed_mps
    return total_s


def _ordinary_local_search_route(
    scenario: Scenario,
    seed: Tuple[str, ...],
    max_passes: int = 30,
) -> Tuple[str, ...]:
    best = tuple(seed)
    best_score = _ordinary_route_objective(scenario, best)

    for _ in range(max_passes):
        improved = False
        candidates = _swap_neighbors(best)
        candidates.extend(_reverse_segments(best))
        for candidate in candidates:
            score = _ordinary_route_objective(scenario, candidate)
            if score + 1e-9 < best_score:
                best = candidate
                best_score = score
                improved = True
                break
        if not improved:
            break

    return best


def _local_search_route(
    scenario: Scenario,
    seed: Tuple[str, ...],
    blackout_weight: float,
    max_passes: int = 30,
) -> Tuple[str, ...]:
    best = tuple(seed)
    best_score = _route_objective(scenario, best, blackout_weight)

    for _ in range(max_passes):
        improved = False
        candidates = _swap_neighbors(best)
        candidates.extend(_reverse_segments(best))

        for candidate in candidates:
            score = _route_objective(scenario, candidate, blackout_weight)
            if score + 1e-9 < best_score:
                best = candidate
                best_score = score
                improved = True
                break

        if not improved:
            break

    return best


def _custom_local_search_route(
    scenario: Scenario,
    seed: Tuple[str, ...],
    objective,
    max_passes: int = 24,
) -> Tuple[str, ...]:
    best = tuple(seed)
    best_score = objective(scenario, best)

    for _ in range(max_passes):
        improved = False
        candidates = _swap_neighbors(best)
        candidates.extend(_reverse_segments(best))

        for candidate in candidates:
            score = objective(scenario, candidate)
            if score < best_score:
                best = candidate
                best_score = score
                improved = True
                break

        if not improved:
            break

    return best


def _metric_baseline_seeds(scenario: Scenario) -> Set[Tuple[str, ...]]:
    return {
        distance_only_route(scenario),
        ordinary_data_collection_route(scenario),
        protocol_aware_route(scenario, blackout_weight=0.0),
        protocol_aware_route(scenario, blackout_weight=3.0),
        protocol_aware_route(scenario, blackout_weight=12.0),
    }


def _average_gap_objective(scenario: Scenario, route: Iterable[str]) -> Tuple[float, float]:
    result = simulate_route(scenario, route)
    metrics = route_temporal_metrics(result)
    return (
        round(metrics.mean_communication_gap_s, 6),
        round(result.total_time_s, 6),
    )


def _freshness_objective(scenario: Scenario, route: Iterable[str]) -> Tuple[float, float]:
    result = simulate_route(scenario, route)
    metrics = route_temporal_metrics(result)
    return (
        round(metrics.mean_collection_completion_s, 6),
        round(result.total_time_s, 6),
    )


def _swap_neighbors(route: Tuple[str, ...]) -> List[Tuple[str, ...]]:
    candidates: List[Tuple[str, ...]] = []
    for left in range(len(route)):
        for right in range(left + 1, len(route)):
            candidate = list(route)
            candidate[left], candidate[right] = candidate[right], candidate[left]
            candidates.append(tuple(candidate))
    return candidates


def _reverse_segments(route: Tuple[str, ...]) -> List[Tuple[str, ...]]:
    candidates: List[Tuple[str, ...]] = []
    for left in range(len(route)):
        for right in range(left + 2, len(route) + 1):
            candidate = route[:left] + tuple(reversed(route[left:right])) + route[right:]
            candidates.append(candidate)
    return candidates


def blackout_focused_route(
    scenario: Scenario,
    max_passes: int = 40,
    seed_max_passes: int = 30,
) -> Tuple[str, ...]:
    """Blackout-first route: minimise maximum blackout, breaking ties by mission
    time. Implemented by forcing the blackout target to zero and using a very
    large blackout weight inside the local search, seeded from several
    constructions so the result is never worse than any seed."""
    from dataclasses import replace

    zero_target = replace(scenario, max_blackout_s=0.0)
    seeds = {
        distance_only_route(scenario),
        protocol_aware_route(scenario, blackout_weight=0.0, max_passes=seed_max_passes),
        protocol_aware_route(scenario, blackout_weight=12.0, max_passes=seed_max_passes),
        protocol_aware_route(zero_target, blackout_weight=30.0, max_passes=seed_max_passes),
    }
    candidates = set(seeds)
    for seed in seeds:
        candidates.add(_local_search_route(zero_target, seed, blackout_weight=1.0e6, max_passes=max_passes))

    def key(route: Tuple[str, ...]):
        result = simulate_route(scenario, route)
        return (round(result.max_blackout_s, 3), round(result.total_time_s, 3))

    return min(candidates, key=key)


def bounded_blackout_route(
    scenario: Scenario,
    budget: float,
    blackout_passes: int = 40,
    seed_max_passes: int = 30,
) -> Tuple[str, ...]:
    """Constrained bounded-blackout planner: among a pool of candidate routes,
    return the fastest route whose maximum blackout is within ``budget``. If no
    candidate meets the budget, return the route with the smallest maximum
    blackout. The hard budget is enforced within the evaluated candidate pool,
    unlike a soft penalty, but this is not a global feasibility guarantee."""
    pool = {
        distance_only_route(scenario),
        ordinary_data_collection_route(scenario),
        protocol_aware_route(scenario, blackout_weight=0.0, max_passes=seed_max_passes),
        protocol_aware_route(scenario, blackout_weight=3.0, max_passes=seed_max_passes),
        protocol_aware_route(scenario, blackout_weight=12.0, max_passes=seed_max_passes),
        blackout_focused_route(
            scenario,
            max_passes=blackout_passes,
            seed_max_passes=seed_max_passes,
        ),
    }
    scored = []
    for route in pool:
        result = simulate_route(scenario, route)
        scored.append((result.max_blackout_s, result.total_time_s, route))

    feasible = [s for s in scored if s[0] <= budget + 1e-6]
    if feasible:
        # fastest route that meets the blackout budget
        return min(feasible, key=lambda s: (s[1], s[0]))[2]
    # infeasible budget: smallest achievable blackout (then fastest)
    return min(scored, key=lambda s: (s[0], s[1]))[2]
