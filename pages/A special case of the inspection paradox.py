import h3
import h3pandas
import pandas as pd
import plotly.graph_objects as go
import geopandas as gpd
import contextily as cx
from shapely.geometry import Polygon
import plotly.express as px
from shapely.wkt import loads
import networkx as nx
import itertools as it
import numpy as np
from sklearn.preprocessing import RobustScaler
import streamlit as st
import h3
import h3pandas
import pandas as pd
import plotly.graph_objects as go
import geopandas as gpd
import contextily as cx
from shapely.geometry import Polygon, LineString, Point, MultiLineString, MultiPoint
import plotly.express as px
from shapely.wkt import loads
import networkx as nx
import itertools as it
import numpy as np
import shapely
from pyproj import Geod
from shapely import ops, geometry
import re
import matplotlib.pyplot as plt
import matplotlib

st.markdown("""
    
    """)

st.markdown("""
Suppose you are tasked with the following problem:
You would like to calculate the fall-out rate of your friendships.
Suppose to make new friends at regular intervals, and your friendships can go on at most 3 years.
In order to calculate the length of your friendship, you need both the start and end dates.
There are two possible ways a friendship can end: amicably and spitefully.
A friendship can end in spite at any given point in the friendship. When a friendship ends in spite, this is called a fall-out.
You would like to calculate the fall-out rate of your friendships, defined as: (# of fall outs)/(# of friendships) across any given interval of time.
Suppose you started gathering data 3 years ago, and have since made X friends and collected their respective start dates.
You were able to observe the outcomes of all X friendships. However, you still would like to use more data.

You have the following option: you are able to reach out to people with whom you were friends with exactly three years ago
(i.e. your friendship began before you began to experiment, but existed during.) You can reach out to them and ask for the start dates of those friendships.
You retrospectively know the outcomes of those friendships, and collecting their start date would allow you to add these observations to your dataset.

The question is: should you do this? You want to keep your observations unbiased.
Is there a way in which you can include this retrospective data without introducing bias? 
""")

st.markdown("""
You might recognize this as survivorship bias. Specifically, as it relates to time, it is a special
base of the bus (or inspection) paradox, which asserts that your measurement of the length of an interval is biased by the fact that
you are more likely to sample from longer intervals. In the case of the bus paradox, this means that the average wait time experienced by a rider is longer than
the average time between stops for the bus driver, because a rider arriving at a bus stop is more likely to encounter delayed schedules.
There is a similar effect in the case of friendships, where your friends tend to be more popular than you are,
because you are more likely to be friends with people who are themselves popular. And of course, there is the classic example of the WWII airplanes, where
the planes which returned from missions were more likely to be the ones which survived, and structural weaknesses were actually more likely to be
in places where the survived planes were not shot. 

Just like the above three examples, your experiment to measure the fall-out rate of your friendships is biased by the fact that you are more likely to sample longer friendships
if you include observations sampled from a single point in time (exactly three years ago). This is because you are more likely to sample friendships that survive longer.
However, you are not trying to sample to average length of a friendship -- you are trying to sample the average outcome.

Ah -- there it is. The real question is: are outcomes independent of the length of a friendship? If so, then it doesn't matter if you sample from a single point in time or not,
since friendships of any length are equally likely to end in a fall-out. This may not be intuitively obvious. You may argue, "still, you
are you are more likely to sample from longer friendships. Therefore, friendships which have already ended in fall-outs are underrepresented in your sample, even though they
may have began at the same time as your current friendships."
# talk about constant hazards in a left-truncated sample

So, we find that: including retrospective data is not biased if the outcome of a friendship is independent of the length of the friendship. However, what if it is? 
Let's consider two possibilities: if the fall-out rate increases over time, and if the fall-out rate decreases over time.
"""
)

st.markdown("## Degrading fall-out rates")
st.markdown("""
Suppose that the risk of fall-out decreases as a function of time. Therefore, the longer a friendship lasts, the less likely it is to end in a fall-out. In other words,
fall-outs are more likely to be observed among the population of new friends than old friends.
""")

st.markdown("## Growing fall-out rates")
st.markdown("""
Suppose that the risk of fall-out increases as a function of time. The longer you are friends with someone, the more likely you are to fall out with them.
How the instantaneous fallâ€‘out hazard Î»(age) behaves
Effect of including the older, leftâ€‘truncated friendships (no age adjustment)
Direction of bias in the naÃ¯ve fallâ€‘out proportion
Hazard increases with age(friendships get more fragile the longer they last)
The extra friendships you import are older and therefore enter the threeâ€‘year window with a higher perâ€‘year risk of ending than the new ones you are primarily interested in.Â  They add a disproportionately large number of fallâ€‘outs to the numerator while counting fully in the denominator.
Bias upward â€“ you will overâ€‘estimate the true fallâ€‘out rate for a cohort of newly formed friendships.
Hazard decreases with age(friendships get more stable over time)
Only the robust friendships survive long enough to appear at baseline; these older ties now carry a lower perâ€‘year risk of ending than brandâ€‘new friendships.Â  They inflate the denominator but contribute relatively few events to the numerator.Â  In addition, the highâ€‘risk early failures that occurred before the study are missing entirely.
Bias downward â€“ you will underâ€‘estimate the true fallâ€‘out rate for newly formed friendships.
""")

st.markdown("## Conclusion")
st.markdown("""
    So, what should you do? Since the reliability of this experiment is dependent on the relationship between the fall-out rate and time, if you resolve the
    functional form of this relationship, then you can back-calculate the bias introduced by including retrospective data, and then you can use this to
    adjust your observations. You can't change the fact that your samples are biased, but you can adjust your analysis to account for it, just
    like how you can choose to add armor to the places where the planes were not shot.
    
    Why this happens
	1.	Left truncation / survivorship selection
A friendship that began before the study is observed only if it survived up to time 0.  Survival to that age is informative whenever λ(age) is not flat.
	2.	No age model ⇒ implicit mixing
By treating all friendships identically in the analysis you implicitly weight the risk set toward older ages.  If older age carries different hazard, the overall event rate you compute is pulled in that direction.
	3.	Direction of distortion
Increasing hazard: older friendships have more future risk ⇒ proportion ends rises.
Decreasing hazard: older friendships have less future risk and early high‑risk ties are missing ⇒ proportion ends falls.

Bottom line
	•	If fall‑out risk rises with friendship age, adding the retrospective ties without modeling age will make the sample look too fragile (over‑estimate).
	•	If fall‑out risk falls with age, the sample will look too durable (under‑estimate).

    """)
st.markdown("""
            The problem of bias hinges greatly on whether the fall-out rate is truly constant over time. A constant fall-out rate means the hazard of a friendship ending is the same at all friendship ages. In survival analysis terms, the friendship duration $T$ would follow an exponential distribution with a constant hazard $\lambda$ (per unit time). A well-known property of the exponential distribution is that it is memoryless: it has no aging effect. Formally, for an exponential distribution, $$P(T > t+s \mid T > s) = P(T > t),$$ meaning that given a friendship has lasted $s$ time units already, the probability it survives an additional $t$ units is the same as if it were brand new ￼. Or in words, “a system surviving at time $t$ forgets how old it is, and so the conditional probability that it survives an additional time $s$ (given it’s survived up to $t$) is the same as the probability of a brand new system surviving $s$” ￼. This “lack of aging” or “memoryless” property uniquely defines the exponential distribution ￼.

Why is this important? Because if friendships truly have a constant hazard (no matter if they are new or years old, their risk of break-up per year is the same), then including the left-truncated friendships need not introduce bias provided we handle the data correctly. Under a constant hazard:
	•	The fact that a retrospective friendship survived to the beginning of the observation period does not make it any less or more likely to end in the next 3 years than a brand-new friendship. In other words, those older friendships “forget” their past and behave like new ones going forward ￼. There is no inherent difference in fall-out probability in the study window between a friendship that’s already 5 years old at baseline and a friendship that formed at baseline, assuming the hazard truly stays constant over time.
	•	Therefore, no systematic bias is introduced by the survivorship selection in terms of estimating the hazard during the observation window. We aren’t selectively including friendships with different forward risk – under the memoryless property, all friendships have identical risk profiles for the future regardless of past duration. This means the retrospective friendships can contribute valid information about the fall-out rate just like the new ones.

However, it is critical that we properly account for their inclusion. In practice, “properly accounting” means we acknowledge their delayed entry into observation. Techniques like survival analysis with left-truncated data (also called late entry) would include these friendships in the risk set only from the time they became observable (time 0) and count their eventual fall-out or censoring accordingly. The constant hazard ensures that this late entry does not distort the estimated hazard. In fact, simulation studies confirm this: when all individuals have the same risk profile (homogeneous hazard), including subjects who enter late (after surviving some time) produces no bias compared to a fully observed cohort ￼. For instance, Applebaum et al. (2011) found “with homogeneous susceptibility, there were no differences between incident (new) and prevalent (left-truncated) subjects” in hazard estimates, whereas heterogeneity in risk did introduce bias ￼.

On the other hand, if the fall-out rate is not constant over time (e.g. friendships become less likely to break up the longer they’ve lasted, or perhaps the risk spikes at certain ages), then including only those friendships that survived to a certain age will bias the estimate. This is because the sample of older friendships is no longer representative of all friendships with respect to risk. For example, if friendships that endure a couple of years are inherently more stable (lower hazard), then the group of pre-existing friendships at baseline is tilted toward these more stable relationships. They would tend to have lower probability of falling out during the study than a random newly formed friendship. Mixing them with new friendships without adjustment would then underestimate the overall fall-out rate (because you added a bunch of long-lasting friendships that are less likely to end). Conversely, if risk increases with time (unlikely in friendship context, but hypothetically), those surviving longer might actually have higher future risk, which could bias the estimate in the opposite direction. The key point is: without the memoryless property, survival up to baseline carries information about the friendship’s risk level, and ignoring that leads to bias.

Including Retrospective Friendships Without Bias

Given the assumption of a constant hazard (memoryless friendship fall-out rate), it is possible to include the retrospective friendships without biasing the fall-out rate estimate,
""")

