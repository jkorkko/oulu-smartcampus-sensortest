# Sensor test
Check and update the status of each sensor in operation. Forward infromation to oulu-smartcampus API.

### Output
Following object for each deveui

{'_id': 'deveui', 'update': {'status': 'status'}}

Where

-deveui: in format "A81758FFFE041FEC"

-status: "online"/"offline"



### Running

You need Python 3.8 and `pip`. The project dependencies are managed with Pipenv.

These commands are run in the repository root:

```sh
cd oulu-smartcampus-sensorstatus
```

1. Install pipenv:

```sh
pip install --user pipenv
```

2. Install project dependencies:

```sh
pipenv install
```

3. Copy example config

```
cp settings.conf.example settings.conf
```

4. Run:

```sh
pipenv shell
```

```sh
python src/main.py
```


### License
Copyright 2020 Jeremias Körkkö under the MIT license
