# Complete Data Dictionary
## Roosevelt National Forest Cover Type Dataset

Dataset: Forest CoverType (USFS Region 2 Resource Information System Data)  
Observations: 581,012 | Predictors: 54 (10 continuous, 4 binary wilderness, 40 binary soil) | Target: 1 (`Cover_Type`)

---

## 1. Continuous Topographic & Distance Predictors (10)

| Column Name | Data Type | Valid Range | Unit | Description & Environmental Interpretation |
|---|---|---|---|---|
| `Elevation` | Integer | [1859, 3858] | Meters | Elevation above sea level. Primary determinant of vegetative zones (tree line ~3,500m). |
| `Aspect` | Integer | [0, 360] | Degrees azimuth | Compass direction the slope faces. North/East aspects are cooler/moister; South/West are hotter/drier. |
| `Slope` | Integer | [0, 66] | Degrees | Slope steepness. Higher slopes increase runoff and accelerate uphill wildfire flame propagation. |
| `Horizontal_Distance_To_Hydrology` | Integer | [0, 1397] | Meters | Horizontal distance to nearest surface water feature (stream, pond, marsh). |
| `Vertical_Distance_To_Hydrology` | Integer | [-173, 601] | Meters | Vertical elevation difference to nearest surface water feature. Negative values indicate location below water feature. |
| `Horizontal_Distance_To_Roadways` | Integer | [0, 7117] | Meters | Horizontal distance to nearest road access. Proxy for human disturbance, accessibility, and fire containment time. |
| `Hillshade_9am` | Integer | [0, 255] | Index | Relative solar radiation index at 09:00 during summer solstice (morning light exposure). |
| `Hillshade_Noon` | Integer | [0, 255] | Index | Relative solar radiation index at 12:00 (midday sun intensity, fuel moisture depletion). |
| `Hillshade_3pm` | Integer | [0, 255] | Index | Relative solar radiation index at 15:00 (afternoon thermal heating). |
| `Horizontal_Distance_To_Fire_Points` | Integer | [0, 7173] | Meters | Horizontal distance to historical wildfire ignition point. Proximity factor in screening models. |

---

## 2. Binary Wilderness Areas (4)

Mutually exclusive binary indicators (one-hot encoded):

| Column Name | Area Name | Characteristics |
|---|---|---|
| `Wilderness_Area1` | Rawah Wilderness | High-elevation wilderness area in Medicine Bow Mountains. Dominated by subalpine spruce-fir. |
| `Wilderness_Area2` | Neota Wilderness | Smallest wilderness area, extremely rugged terrain, glacial cirques and high elevation alpine ecosystems. |
| `Wilderness_Area3` | Comanche Peak Wilderness | Surrounds Rocky Mountain National Park. Diverse elevation range with lodgepole pine and alpine tundra. |
| `Wilderness_Area4` | Cache la Poudre Wilderness | Lower elevation river canyon ecosystem dominated by Ponderosa Pine and Douglas-fir. |

---

## 3. Binary Soil Types (40)

Binary indicator variables (`Soil_Type1` through `Soil_Type40`) derived from USFS soil survey units. They encode rock outcrop presence, soil depth, stony texture, and parent geologic material (granitic, alluvium, colluvium).

---

## 4. Target Variable: `Cover_Type`

Integer categorical label [1 to 7] representing dominant forest tree species:

| Class ID | Species Name | Scientific Name | Total Count | % of Dataset | Dominant Habitat |
|---|---|---|---|---|---|
| **1** | Spruce / Fir | *Picea engelmannii / Abies lasiocarpa* | 211,840 | 36.46% | High elevation subalpine (2,700m–3,400m), moist soils |
| **2** | Lodgepole Pine | *Pinus contorta* | 283,301 | 48.76% | Mid-to-high elevation (2,500m–3,100m), post-fire seral stands |
| **3** | Ponderosa Pine | *Pinus ponderosa* | 35,754 | 6.15% | Lower montane (1,800m–2,600m), dry, fire-adapted |
| **4** | Cottonwood / Willow | *Populus deltoides / Salix spp.* | 2,747 | 0.47% | Riparian valleys, streamsides, lowest elevation (<2,300m) |
| **5** | Aspen | *Populus tremuloides* | 9,493 | 1.63% | Moist slopes, forest openings, disturbance succession |
| **6** | Douglas-fir | *Pseudotsuga menziesii* | 17,367 | 2.99% | North-facing lower slopes, rocky terrain (2,000m–2,800m) |
| **7** | Krummholz | Stunted alpine tree line ecotone | 20,510 | 3.53% | Extreme alpine winds, harsh cold, highest elevation (>3,300m) |
