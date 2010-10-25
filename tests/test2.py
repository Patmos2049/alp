#!/usr/bin/env python
# Use the alp module to print the Alp time "tomorrow"

import alp
alp.set_start_date(alp.alp_to_datetime(
        alp.time.alp + 1, alp.time.hexalp, alp.time.qvalp,
        alp.time.salp, alp.time.talp, alp.time.second))
alp.update()
print alp.time
