# TC-3-P-PPC The Energy Market
## 1. Goal
design and implement a multi-process and multi-thread
simulation in Python.
## 2. Presentation
### Minimum specifications: (4 processes)
* `home`:
* * 1. always give away
* * 2. always sell on the market
* * 3. sell on the market if no takers
* `market`:
* * **price** depends on transactions with **homes** (selling and buying), **weather conditions** and **random events**.
* `weather`: impacting energy consumption.
* * temperature
* * temperature variation over time
* `external`: random eventsthat can impact the energy price.
* at least 1 internal and 1 external factors: 
* * * internal: **temperature**
* * * external: **gaz shortage**
### Technical specifications:
* `home` ---message queue---> `home`
* `home` ---sockets---> `market`
* `weather` ---shared memory---> `home` & `market`
* `market`<===child===`external`---signals--->`market`
* `home` & `market` ==> **display progress**
### Energy price: linear model
$$ P_t = \gamma P_{t-1} +  \sum_i \alpha_i f_{i,t} + \sum_j \beta_j u_{j,t} $$
$$ Price_{current} = Coef_\gamma * Price_{last} + Coef_\alpha * Internal-Factor_{all-time} + Coef_\beta * External-Factor_{all-time} $$
### Other specifications:
* Automate the startup and the proper shutdown of the simulation, freeing all resources.
* Identify possible failure scenarios 
* Think about recovery or termination strategies.
## 3. Solution


