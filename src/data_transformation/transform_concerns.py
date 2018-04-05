# Transform a concerns CSV into compatible JSON document.
# Author terryf82 https://github.com/terryf82

import argparse
import dateutil.parser as date_parser
import json
import os
import pandas as pd
from collections import OrderedDict
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--destination", type=str,
                    help="destination name")
parser.add_argument("-f", "--folder", type=str,
                    help="absolute path to destination folder")

args = parser.parse_args()

raw_path = os.path.join(args.folder, "raw")
if not os.path.exists(raw_path):
    print raw_path+" not found, exiting"
    exit(1)

valid_concerns = []
manual_concern_id = 1

print "searching "+raw_path+" for raw concerns file(s)"

for csv_file in os.listdir(raw_path):
    print csv_file


    df_concerns = pd.read_csv(os.path.join(raw_path, csv_file), na_filter=False)
    dict_concerns = df_concerns.to_dict("records")

    for key in dict_concerns:
        if args.destination == "boston":
            # Boston presently has concerns from two sources - VisionZero and SeeClickFix
            if csv_file == "Vision_Zero_Entry.csv":
                source = "visionzero"
                # skip concerns that don't have a date or request type
                if key["REQUESTDATE"] == "" or key["REQUESTTYPE"] == "":
                    continue

                else:
                    valid_concern = OrderedDict([
                        ("id", key["OBJECTID"]),
                        ("source", "visionzero"),
                        ("dateCreated", key["REQUESTDATE"]),
                        ("status", key["STATUS"]),
                        ("category", key["REQUESTTYPE"]),
                        ("location", OrderedDict([
                            ("latitude", key["Y"]),
                            ("longitude", key["X"])
                        ]))
                    ])

                    # only add summary property if data exists
                    if key["COMMENTS"] != "":
                        valid_concern.update({"summary": key["COMMENTS"]})

            elif csv_file == "bos_scf.csv":
                source = "seeclickfix"
                # skip concerns that don't have a date or request type
                if key["created"] == "" or key["summary"] == "":
                    continue

                else:
                    valid_concern = OrderedDict([
                        ("id", manual_concern_id),
                        ("source", "seeclickfix"),
                        ("dateCreated", key["created"]),
                        ("status", "unknown"),
                        ("category", key["summary"]),
                        ("location", OrderedDict([
                            ("latitude", key["Y"]),
                            ("longitude", key["X"])
                        ]))
                    ])

                    # only add summary property if data exists
                    if key["description"] != "":
                        valid_concern.update({"summary": key["description"]})

            valid_concerns.append(valid_concern)
            manual_concern_id += 1

        if args.destination == "dc":
            # skip concerns that don't have a date or request type
            if key["REQUESTDATE"] == "" or key["REQUESTTYPE"] == "":
                continue

            valid_concern = OrderedDict([
                ("id", key["OBJECTID"]),
                ("dateCreated", key["REQUESTDATE"]),
                ("status", key["STATUS"]),
                ("category", key["REQUESTTYPE"]),
                ("location", OrderedDict([
                    ("latitude", key["Y"]),
                    ("longitude", key["X"])
                ]))
            ])

            # only add summary property if data exists
            if key["COMMENTS"] != "":
                valid_concern.update({"summary": key["COMMENTS"]})

            valid_concerns.append(valid_concern)

        elif args.destination == "cambridge":
            # skip concerns that don't have a date or issue type
            if key["ticket_created_date_time"] == "" or key["issue_type"] == "":
                continue

            valid_concern = OrderedDict([
                ("id", key["ticket_id"]),
                ("dateCreated", datetime.strftime(date_parser.parse(key["ticket_created_date_time"]), "%Y-%m-%dT%H:%M:%S")+"-05:00"),
                ("status", key["ticket_status"]),
                ("category", key["issue_type"]),
                ("location", OrderedDict([
                    ("latitude", key["lat"]),
                    ("longitude", key["lng"])
                ]))
            ])

            # only add summary property if data exists
            if key["issue_description"] != "":
                valid_concern.update({"summary": key["issue_description"]})

            valid_concerns.append(valid_concern)

print "done, {} valid concerns loaded".format(len(valid_concerns))

concerns_output = os.path.join(args.folder, "transformed/concerns.json")

with open(concerns_output, "w") as f:
    json.dump(valid_concerns, f)

print "output written to {}".format(concerns_output)
