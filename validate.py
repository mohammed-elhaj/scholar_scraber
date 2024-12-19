import json
import os
from jsonschema import validate, ValidationError

# Define the expected JSON schema
expected_schema = {
    "type": "object",
    "properties": {
        "scholarship": {
            "type": "object",
            "properties": {
                "basic_info": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "post_date": {"type": "string"},
                        "author": {"type": "string"},
                        "funding_type": {"type": "string"},
                        "host_countries": {"type": "array"},
                        "program_name": {"type": "string"},
                        "funded_by": {"type": "string"},
                        "degree_levels": {"type": "array"},
                        "duration": {"type": "string"},
                        "scholarships_available": {"type": "string"},
                        "deadline": {"type": "string"}
                    },
                    "required": ["title", "post_date", "author", "funding_type", "host_countries", "program_name", "funded_by", "degree_levels", "duration", "scholarships_available", "deadline"]
                },
                "program_details": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "study_locations": {"type": "array"},
                        "participating_universities": {"type": "array"},
                        "program_structure": {
                            "type": "object",
                            "properties": {
                                "year_1": {"type": ["string", "null"]},
                                "year_2": {"type": ["string", "null"]}
                            }
                        },
                        "subjects": {"type": "array"}
                    },
                    "required": ["description", "study_locations", "participating_universities", "program_structure", "subjects"]
                }
            },
            "required": ["basic_info", "program_details"]
        }
    },
    "required": ["scholarship"]
}

def convert_none_to_empty_string(data):
    if isinstance(data, dict):
        return {k: convert_none_to_empty_string(v) if v is not None else "" for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_none_to_empty_string(v) if v is not None else "" for v in data]
    else:
        return data

def validate_json_structure(file_path, schema):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        data = convert_none_to_empty_string(data)
        try:
            validate(instance=data, schema=schema)
            return True, data
        except ValidationError as e:
            return False, data

def combine_json_files(valid_example, invalid_files, output_file):
    combined_data = {"valid_example": valid_example, "invalid_files": invalid_files}
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(combined_data, file, ensure_ascii=False, indent=4)

def main():
    directory = 'scholarships'
    valid_example = None
    invalid_files = []

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            is_valid, data = validate_json_structure(file_path, expected_schema)
            if is_valid and valid_example is None:
                valid_example = data
            elif not is_valid:
                invalid_files.append(data)

    if valid_example is not None and invalid_files:
        combine_json_files(valid_example, invalid_files, 'combined_output.json')
        print("Combined JSON file created: combined_output.json")
    else:
        print("No valid example found or no invalid files to combine.")

if __name__ == "__main__":
    main()