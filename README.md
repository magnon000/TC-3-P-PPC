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

> Price(current) = Coef1 * Price(last) + Coef2 * Internal-Factor(all-time) + Coef3 * External-Factor(all-time)
### Other specifications:
* Automate the startup and the proper shutdown of the simulation, freeing all resources.
* Identify possible failure scenarios 
* Think about recovery or termination strategies.
## 3. Solution
### PROCESSES :
- plusieurs petits processes `home` qui se lancent directement depuis le terminal (agit comme les clients dans les TD).
- 1 process `market` qui se lance directement (agit comme le serveur dans les TD) idéal à lancer en premier.
- 1 process `external` fils de `market` comme expliqué dans l'énoncé.
- 1 process `weather` qui se lance directement depuis le terminal (OU pourquoi pas fils de `market` ? => PARCE QUE LES `home`s SONT AUSSI IMPACTEES PAR LA TEMPERATURE ETC)

### `home` to `home`
`MESSAGES QUEUES`: 

**A déterminer : **
* 1 message queue qui agit comme une sorte de pipe entre chaque maison ? 
* Ou une message queue globale avec les propositions de don des maisons productrices que les maisons réceptrices peuvent sémaphorer et accepter ?
Le second choix est mieux je pense.

Par contre, deux informations contradictoires :
> Homes in need of energy will have to buy it from the market if others would not give away any. 
> 
> Type 3 homes sell energy on the market if no takers.

**Comment concilier ces deux ?**

Est-ce le donneur qui initie l'échange en proposant de l'énergie à tout le monde (oui)

ou est-ce le receveur qui initie l'échange en demandant de l'énergie à tout le monde ? (choisi: non)

Dans tous les cas, je pense qu'il ne faut pas que les maisons ATTENDENT de l'énergie de la part des autres maisons.

=> SOLUTION TROUVEE : QUE LES PRODUCERS QUI POUSSENT DANS LA MESSAGE QUEUE (& peuvent reprendre leur message dans le cas de 3).

**POINT 1**====> Aussi, modèle `gourmand & égoiste` : si assez d'énergie disponible dans la message queue, la maison va se servir
de tous les dons jusqu'à être compensé en consommation sans partager.(premier arrivé premier servi)

Pour changer ça intervertir semaphore et boucle là où c'est écrit.

**POINT 2**====> + modèle donner c'est donner reprendre c'est voler = producteur qui devient consommateur n'a pas la priorité
sur la message queue, il attend comme tout le monde et ne reprend pas forcément ce qu'il a mis sur la queue.

**POINT 3**===>>> IMPORTANT : modèle `MECHANT` => une maison se sert dans la message queue. Si elle obtient plus que
nécessaire, elle garde ce surplus pour elle et le gère selon son type I II ou III (grâce au thread séparation).

Pour changer ça, le surplus obtenu de la message queue ne doit pas être enregistré dans les stats globales.


========================>>>>> J'ai fait plusieurs tests et il semble que sysv_ipc intègre déjà dans ses
fonctions recieve et send un mutex. Car quand on met deux clients attendant sur une message queue et qu'on envoie
sur la message queue des messages, celui qui le reçoit change d'un message sur l'autre.

Mais je `sémaphore` quand même par précaution l'accès à la message queue (que ce soit écriture ou lecture).

Cela permet d'implémenter le modèle gourmand & égoiste.

Pour le type : puissance partagée en int peut-être ? je ne sais pas. mettre à profit l'attribut 'type' des messages queues.

ON SE SERT DES TYPES DE MESSAGE DANS MESSAGE QUEUE POUR ENELVER SON MESSAGE LORSQUE AUCUN DONNEUR.

=> Donc

Résumé : modèle `gourmand` (les maisons prendent plus que nécessaire plutôt que moins), `égoiste` (dès qu'une maison a l'accès
elle ne le lâche pas tant qu'elle n'est pas rassasiée) et `méchant` (le surplus obtenu par gourmandise est traité comme
une production personnelle.


### SOCKETS : chaque `home` ----> `market`
- c'est sûrement les maisons qui initient le contact avec le marché car ils ne produisent pas assez ou pas du tout.
(après avoir demandé aux autres maisons selon leur type)
- voir pour le type.

### SHARED MEMORY : sert au `weather` process
* remote manager
  
Je dirais plutôt des Values que des Arrays... 1 value température, une value météo etc.

"how they are accessed" ??? je sais pas

### SIGNALS : `external` ----> `market`
On utilisera sûrement les signaux personnalisés (SIGUSER1 ou je sais plus quoi).

le marché saura le décrypter.

### TUBES : ???? ce n'est pas expliqué dans l'énoncé

=> D'après conversation entendue : 1 signal vers `market` depuis `external` pour lui dire de lire dans la pipe, puis évènement spécifique spécifié dans la pipe.

---
### extra:
* `market`: consumption up, demand up, price up
* `home`: price up, consumption down
* `weather`: ex. rain -> proba to cause an event ext
* 


