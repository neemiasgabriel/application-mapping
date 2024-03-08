import json

def generate_csv(file_name, csv_matrix):
  rows = ["{},{},{}".format(i, j, k) for i, j, k in csv_matrix]
  text = "\n".join(rows)

  with open(f'files/{file_name}.csv', 'w') as f:
    f.write(text)

def generate_csv_bootstrap(file_name, csv_matrix):
  rows = ["{},{},{}".format(i, j, k) for i, j, k in csv_matrix]
  text = "\n".join(rows)

  with open(f'files/{file_name}.csv', 'w') as f:
    f.write(text)


def generate_csv_application(file_name, csv_matrix):
  rows = ["{},{},{},{},{}".format(i, j, k, l, m) for i, j, k, l, m in csv_matrix]
  text = "\n".join(rows)

  with open(f'files/{file_name}.csv', 'w') as f:
    f.write(text)

def save_dictionary(projects_dict, file_name):
  with open(f'files/{file_name}.json', 'w') as f:
    try:
      json.dump(projects_dict, f)
    except json.decoder.JSONDecodeError:
      print(projects_dict)

def load_dictionary(path):
  with open(path, 'a+') as f:
    try:
      return json.load(f)
    except json.decoder.JSONDecodeError:
      return None

def load_file(file_path):
  with open(file_path, 'r') as f:
    try:
      return json.load(f)
    except json.decoder.JSONDecodeError:
      return None