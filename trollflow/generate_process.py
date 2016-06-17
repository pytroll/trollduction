from trollflow.workflow_launcher import WorkflowStreamer


def generate_daemon(config_item):
    return config_item['components'][-1]['class']

def generate_workflow(config_item):
    wfs = WorkflowStreamer(config=config_item)
    wfs.start()
    return wfs


import yaml

path_to_workflow = 'test/flow.yaml'
with open(path_to_workflow, "r") as fid:
    config = yaml.load(fid)

types = {'daemon': generate_daemon,
         'workflow': generate_workflow}

workers = []

for item in config['work']:
    workers.append(types[item['type']](item))

queue = None
for worker in workers:
    if queue is not None:
        worker.input_queue = queue
    queue = worker.output_queue
