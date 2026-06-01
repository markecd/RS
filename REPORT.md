Task1

| CU | Kernel  | Load Latency | vALUInsts | ldsBankAccess | Total Cycles | VPC   |
|----|---------|--------------|-----------|---------------|--------------|-------|
|  2 | naive   |   6086404.05 |     22528 |             0 |       830584 | 3.787 |
|  2 | opt     |    811769.04 |     28672 |        393216 |       229760 | 21.678 |
|  4 | naive   |  12390140.75 |     11264 |             0 |       808835 | 1.945 |
|  4 | opt     |   1663198.85 |     14336 |        196608 |       177303 | 14.046 |
|  8 | naive   |  23988775.51 |      5632 |             0 |       786332 | 1.000 |
|  8 | opt     |   4072869.63 |      7168 |         98304 |       172969 | 7.199 |




Task2

| CU | Kernel  | Load Latency | vALUInsts | ldsBankAccess | Total Cycles | VPC   |
|----|---------|--------------|-----------|---------------|--------------|-------|
|  2 | naive   |   8116740.97 |     36864 |             0 |       528799 | 7.436 |
|  2 | opt     |   2584615.23 |     53248 |        262144 |       314736 | 22.073 |
|  4 | naive   |  18799825.68 |     18432 |             0 |       573771 | 3.427 |
|  4 | opt     |   5884136.23 |     26624 |        131072 |       318606 | 10.902 |
|  8 | naive   |  42548443.36 |      9216 |             0 |       669589 | 1.468 |
|  8 | opt     |  12564341.06 |     13312 |         65536 |       317917 | 5.463 |


Naive implementacija bere row-oriented matriko v pomnilniku zaporedno vendar ker gre za transponiranje mora
pisati v obratnem pise v b matriko po stolpcih pri cemer mora pisati s preskokom pomnilniskih mest ker pa zaradi preskoka zaporedna pisanja in torej sosednje niti ki pišejo isti čas ne padejo v isto cache linijo pride do veliko cache missov. In takšno non-coalesced pisanje pri večih CU/SM zaradi vedno več vzporednih cache missov hitro zasičimo l2 cache, ki je za gpu globalen tako da izvajalni čas z dodajanjem SM dejansko raste.

Optimalna implementacija kot buffer izkoristi lds/shared memory pri cemer enako bere matriko zaporedno po vrsticah in to shrani v lds. Iz zelo hitrega lds pa potem sicer z non-coalesced branjem z obrnitvijo x in y dimenzije threada ki dolocata stolpec in vrstico v matriki pri čemer sedaj niti istega warpa pišejo v isto vrstico pisemo v ciljno matriko stolpce zaporedno pri cemer pa lahko zaradi trika zaporedni stolpci padejo v isto cache linijo.


