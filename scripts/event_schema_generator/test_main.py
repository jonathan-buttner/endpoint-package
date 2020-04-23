import main
import yaml
import pytest

base_yaml = '''
base:
  description: The `base` field set contains all fields which are on the top level.
    These fields are common across all types of events.
  fields:
    '@timestamp':
      dashed_name: '@timestamp'
      description: 'Date/time when the event originated.

        This is the date/time extracted from the event, typically representing when
        the event was generated by the source.

        If the event source has no original timestamp, this value is typically populated
        by the first time the event was received by the pipeline.

        Required field for all events.'
      example: '2016-05-23T08:05:34.853Z'
      flat_name: '@timestamp'
      level: core
      name: '@timestamp'
      normalize: []
      required: true
      short: Date/time when the event originated.
      type: date
    message:
      allowed_values:
         - description: 'Events in this category are related to the challenge and response
               process in which credentials are supplied and verified to allow the creation
               of a session. Common sources for these logs are Windows event logs and ssh
               logs. Visualize and analyze events in this category to look for failed logins,
               and other authentication-related activity.'
           expected_event_types:
             - name: 1
             - name: 2
           name: authentication
         - description: 'The database category denotes events and metrics relating to
               a data storage and retrieval system. Note that use of this category is not
               limited to relational database systems. Examples include event logs from
               MS SQL, MySQL, Elasticsearch, MongoDB, etc. Use this category to visualize
               and analyze database activity such as accesses and changes.'
           expected_event_types:
             - name: a
             - name: b
           name: database
      dashed_name: message
      description: 'For log events the message field contains the log message, optimized
        for viewing in a log viewer.

        For structured logs without an original message field, other fields can be
        concatenated to form a human-readable summary of the event.

        If multiple messages exist, they can be combined into one message.'
      example: Hello World
      flat_name: message
      level: core
      name: message
      normalize: []
      norms: false
      short: Log message optimized for viewing in a log viewer.
      type: text
  group: 1
  name: base
  prefix: ''
  root: true
  short: All fields defined directly at the top level
  title: Base
  type: group
'''


def test_gather_fields_constructs_correct_mapping_from_dict():
    base_dict = yaml.safe_load(base_yaml)
    actual = main.gather_fields('base', base_dict['base'])
    exp = {
        'name': 'base',
        'description': base_dict['base']['description'],
        'fields': [
            {
                'name': '@timestamp',
                'type': 'date',
                'description': base_dict['base']['fields']['@timestamp']['description'],
                'example': '2016-05-23T08:05:34.853Z'
            },
            {
                'name': 'message',
                'type': 'text',
                'description': base_dict['base']['fields']['message']['description'],
                'example': 'Hello World',
                'allowed_values': main.reorder_fields(base_dict['base']['fields']['message']['allowed_values'])
            },

        ]
    }
    assert actual == exp


dotted_yaml = '''
endpoint:
  description: Fields describing the state of the Elastic Endpoint when an event occurs.
  fields:
    file:
      description: Extended "file" field set
      level: custom
      name: file
    file.original:
      description: Original file information during a modification event.
      level: custom
      name: file.original
    file.original.gid:
      description: Primary group ID (GID) of the file.
      example: '1001'
      level: custom
      name: file.original.gid
      type: keyword
'''


def test_expand_dots_converts_to_dict_no_dots():
    dotted_dict = yaml.safe_load(dotted_yaml)
    exp = {
        'endpoint': {
            'name': 'endpoint',
            'description': dotted_dict['endpoint']['description'],
            'fields': {
                'file': {
                    'name': 'file',
                    'description': 'Extended "file" field set',
                    'level': 'custom',
                    'fields': {
                        'original': {
                            'name': 'file.original',
                            'description': 'Original file information during a modification event.',
                            'level': 'custom',
                            'fields': {
                                'gid': {
                                    'name': 'file.original.gid',
                                    'description': 'Primary group ID (GID) of the file.',
                                    'example': '1001',
                                    'level': 'custom',
                                    'type': 'keyword'
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    assert main.expand_dots(dotted_dict) == exp


schema_yaml = '''
title: driver
fields:
  - name: endpoint
    description: tODo
    fields:

      - name: group
        description: Extended "group" field set
        fields:

          - name: real
            description: Group info prior to any setgid operations.
            fields:

              - name: id
                type: keyword
                description: toDO

              - name: name
                type: keyword
                description: TODO
'''


def test_recurse_fields_for_enrichment(mocker):
    fake_desc = 'Awesome description'
    mocked_get_schema_desc = mocker.patch('main.get_schema_desc')
    mocked_get_schema_desc.return_value = fake_desc
    schema_dict = yaml.safe_load(schema_yaml)
    desc_info = {
        'endpoint': True,
        'id': True
        # name is not in here and should stay as TODO
    }
    exp = {
        'title': 'driver',
        'fields': [
            {
                'name': 'endpoint',
                'description': fake_desc,
                'fields': [
                    {
                        'name': 'group',
                        'description': 'Extended "group" field set',
                        'fields': [
                            {
                                'name': 'real',
                                'description': 'Group info prior to any setgid operations.',
                                'fields': [
                                    {
                                        'name': 'id',
                                        'type': 'keyword',
                                        'description': fake_desc
                                    },
                                    {
                                        'name': 'name',
                                        'type': 'keyword',
                                        'description': 'TODO'
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    main.recurse_fields(schema_dict['fields'], desc_info)
    assert schema_dict == exp