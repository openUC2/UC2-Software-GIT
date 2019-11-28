# Small Scripts to help setting-up or fix your RasPi

## Setting up Python UC2env
The description on how to setup the python environment with Berryconda (a Anaconda derivate for RasPi) can be found [here](./SETUP_UC2env). 

## Fixing the date-error
Typically RasPi refuses to get new updates or even access to internet if time-settings are heavily wrong. Adding ntp as well as ntpd services to invoke auto-updates do only work from time to time, hence we chose to offer two ways: 
1. enter date and time manually (works offline) -> [here](./FIX_date)
2. add cron-job to get correct time (needs internet connection) -> [here](./FIX_date)