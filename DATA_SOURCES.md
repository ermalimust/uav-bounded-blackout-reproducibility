# External Data Sources

This package uses public measurement evidence to set scheduler-visible protocol-profile fields. The external datasets and papers should be accessed from their original repositories, DOIs, or source pages. Raw third-party datasets are not redistributed in this repository.

## Measurement-Informed Profile Role

The diagnostic profiles map reported measurement envelopes into routing-simulator inputs:

- reported PDR/range envelopes inform the nominal contact range;
- residual near-edge non-delivery is represented as the edge-loss term;
- setup, reconnect, and timing fields use scheduler assumptions informed by measurement studies, protocol semantics, or local bench-scale checks where public aerial data are unavailable.

These mappings are profile inputs for a route evaluator. They are not fitted deployment models, do not uniquely identify every numerical constant, and do not constitute closed-loop UAV validation.

## LoRa and LoRaWAN Sources

- Joachim Tapparel and Andreas Burg, *Dataset and UAV Propagation Channel Modeling for LoRa in the 860 MHz ISM Band*, arXiv:2512.15268.
- Sergio Vargas Villar, Simran Singh, Ozgur Ozdemir, Mihail L. Sichitiu, and Ismail Guvenc, *Real-World LoRaWAN Performance and Propagation Modeling Using UAV, Helikite, and Vehicle-Based Measurements*, arXiv:2604.06444.
- Laksh Bhatia, Michael Breza, Ramona Marfievici, and Julie A. McCann, *LoED: The LoRaWAN at the Edge Dataset*, Zenodo DOI: 10.5281/zenodo.4121430.

Used fields:

- nominal LoRa contact range;
- low-rate LoRa service envelope;
- near-edge loss allowance;
- aerial-link variability check.

## ZigBee-Class IEEE 802.15.4 Sources

- Michael Nekrasov, Ryan Allen, and Elizabeth Belding, *Performance Analysis of Aerial Data Collection from Outdoor IoT Sensor Networks using 2.4GHz 802.15.4*, DOI: 10.1145/3325421.3329769.
- Companion public aerial measurement dataset: Dryad DOI: 10.25349/D9KS3W.

Used fields:

- nominal ZigBee-class contact range;
- near-edge loss allowance;
- aerial range-collapse evidence.

## BLE and Wi-Fi Fields

No public aerial BLE or Wi-Fi IoT dataset was used. These fields are bounded by ground measurement studies, standard protocol semantics, and local bench-scale service-time checks. They are included so that the heterogeneous profile remains complete; the externally grounded aerial evidence is limited to the LoRa and ZigBee-class envelopes.

## Reproducibility Note

The checked-in CSV files record the measurement-informed protocol table and the resulting route metrics. The script `experiments/run_public_measurement_profile.py` regenerates the public-measurement profile outputs from the values embedded in `src/uav_protocol_planning/scenarios.py`.
