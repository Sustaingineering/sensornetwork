import thingspeak_bulk_update
import os

api_key = os.environ.get('THINGSPEAK_KEY', None)
ch_id = os.environ.get('THINGSPEAK_CH_ID', None)

ch = thingspeak_bulk_update.Channel(id = ch_id, api_key = api_key)

test_data = {
    "updates" : [{
        "delta_t" : 5,
        "field1" : 5,
    },
    {
        "delta_t" : 7,
        "field1" : 7,
    }]
}

ch.bulk_update(data = test_data)