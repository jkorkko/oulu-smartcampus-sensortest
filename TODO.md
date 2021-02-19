!! is smarcampus manage: `device.deviceId` is deveui
!! `device._id` is an internal unique identifier used by the MongoDB database

- only send updates devices that are installed (ignore mainentance, planned)

- avoid updating devices that haven't changed

- allow limiting updates to just one sensor (for development safety)

- validate online_query

- send update requests (POST /devices/update)
