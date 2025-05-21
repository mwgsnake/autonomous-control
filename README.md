# Autonomous Security Control on NGINX
This project shows how multiple different types of security controls can get combined to form a new type of security control. Here we combine "detective", "compensative", "corrective" control types to become a "preventive" control. In total we might call this "autonomous security control", which manages the healthiness of a webservice.

In this project there are the following elements being used:
* NGINX image
* Tensorflow Machine Learning
* streamlit_ui
* custom_rules.conf (read by the nginx.conf using include)

The elements represent the following security controls:
detective - NGINX access.log
compenative - ML / Tensorflow training with normal traffic data
corrective - rule management of: custom_rules.conf
preventive - NGINX use of block list

## Installation

## Purpose
This project shall demonstrate how easy it would be to design an autonomous security control and therefore acts as motivator for developers and solution designers to incorporate similar security controls into any application they would be designing.

