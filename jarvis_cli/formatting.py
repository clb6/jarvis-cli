import copy

def format_event(event, max_length=80):
    event_copy = copy.deepcopy(event)
    description = event_copy["description"]
    event_copy["description"] = "{0}..".format(description[:max_length]) \
            if len(description) > max_length else description
    return event_copy

def format_event_request(event_request, max_length=80):
    return format_event(event_request, max_length)
