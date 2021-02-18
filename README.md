# Sensor test
Check and update the status of each sensor in operation. Forward infromation to oulu-smartcampus API.

### Output
Following object for each deveui

{'_id': '<deveui>', 'update': {'status': '<status>'}}

Where
- deveui format: "A81758FFFE031010"
- status: "offline"/"online"

### License
Copyright 2020 Jeremias Körkkö under the MIT license
