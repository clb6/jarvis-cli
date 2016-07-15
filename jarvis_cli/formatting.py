import copy

def truncate_long_text(some_text, max_length=80):
    return "{0}..".format(some_text[:max_length]) \
            if len(some_text) > max_length else some_text

def format_event(event, max_length=80):
    event_copy = copy.deepcopy(event)
    description = event_copy["description"]
    event_copy["description"] = truncate_long_text(description, max_length)
    return event_copy

def format_event_request(event_request, max_length=80):
    return format_event(event_request, max_length)
