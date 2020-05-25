import requests
from datetime import datetime, timedelta
import settings
import logging

logger = logging.getLogger(__name__)

class GitLab():

  def __init__(self):
    self.api = settings.GITLAB_API_URL    # instance variable unique to each instance
    self.gl_session = requests.Session()
    self.gl_session.headers = {
      'PRIVATE-TOKEN': settings.GITLAB_TOKEN
    }
    self.gl_session.verify=True

  # We want to see the last 2 weeks
  def timespan(self):
    return datetime.now() - timedelta(days=14)

  def get_request(self, endpoint):
    url = self.api + endpoint
    logger.debug("GitLab request: " + url)  
    response = self.gl_session.get(url = url)

    if response.status_code != 200:
      raise Exception(response.text)
    return response

  def get_all_pages(self, endpoint):
    retval = []
    query_separator = '&' if endpoint.find('?') != -1 else '?'

    page_index = 1
    next = True
    while next == True:
      
      response = self.get_request(endpoint + query_separator + 'page={}&per_page=100'.format(page_index) )
      retval = retval + response.json()

      if 'X-Next-Page' in response.headers and not response.headers['X-Next-Page']:
        next = False
      if 'X-Next-Page' in response.headers and response.headers['X-Next-Page']:
        if int(response.headers['X-Next-Page']) <= page_index:
          next = False
      if 'X-Next-Page' not in response.headers:
        next = False
      page_index = page_index + 1
    return retval

  ##########################################################

  def get_group_name(self, group_id):
    return self.get_request('/groups/{}'.format(group_id)).json()['name']

  def get_project_name(self, project_id):
    return self.get_request('/projects/{}'.format(project_id)).json()['name']

  ##########################################################

  def get_commits(self, project_id):
    issues = self.get_all_pages('/projects/{}/repository/commits?ref_name=master&since={}'.format(project_id, self.timespan()))
    retval = [dict(issue, **{'project_id': project_id}) for issue in issues]
    return retval

  ##########################################################

  def get_issues(self, group_id, search):
    issues = self.get_all_pages('/groups/{}/issues?{}&scope=all'.format(group_id, search))
    retval = issues
    return retval

  ##########################################################

  def get_weights(self, group_id, search):
    issues = self.get_issues(group_id, search) # 'milestone={}'.format(milestone_title)
    
    total_issue_weight = 0
    closed_issue_weight = 0
    for issue in issues:
      issue_id = issue['id']
      issue_state = issue['state']

      # Weights
      issue_weight = (issue['weight'] if issue['weight'] is not None else 0)
      total_issue_weight += issue_weight
      if issue_state == 'closed' and issue_weight > 0:
        closed_issue_weight += issue_weight
    return { 'total': total_issue_weight, 'closed': closed_issue_weight }

  def no_upcoming_milestones_predicate(self, milestone):
    today = datetime.now().strftime("%Y-%m-%d")
    return (milestone['due_date'] >= today and milestone['start_date'] < today) or milestone['state'] == 'closed'
    
  def sort_by_milestone_title(self, milestone):
    return milestone['title']

  def get_milestones(self, group_id):
    milestones = self.get_all_pages('/groups/{}/milestones?search=Sprint'.format(group_id))
    milestones = list(filter(self.no_upcoming_milestones_predicate, milestones))
    milestones.sort(key=self.sort_by_milestone_title)
    milestones = milestones[-5:]

    retval = []
    for milestone in milestones:
      milestone_id = str(milestone['id'])
      issues = self.get_all_pages('/groups/{}/milestones/{}/issues'.format(group_id, milestone_id))
      retval = retval + issues
    retval = retval
    return retval

  ##########################################################

  def get_pipelines(self, project_id):
    pipelines = self.get_all_pages('/projects/{}/pipelines?ref=master&scope=finished&updated_after={}'.format(project_id, self.timespan()))
    
    retval = []
    for pipeline in pipelines:
      pipeline_id = pipeline['id']       
      pipeline_details = pipeline.copy()

      detail = self.get_request('/projects/{}/pipelines/{}'.format(project_id, pipeline_id)).json()
      test_report = self.get_request('/projects/{}/pipelines/{}/test_report'.format(project_id, pipeline_id)).json()

      # Add project id
      pipeline_details.update({'project_id': project_id})

      # Add coverage details
      coverage = detail['coverage'] if detail['coverage'] is not None else 0
      pipeline_details.update({'duration':'{}'.format(detail['duration'])})
      pipeline_details.update({'coverage': float(coverage)})

      # Add test report details
      pipeline_details.update({'total_time': test_report['total_time']})
      pipeline_details.update({'total_count': test_report['total_count']})
      pipeline_details.update({'success_count': test_report['success_count']})
      pipeline_details.update({'failed_count': test_report['failed_count']})
      pipeline_details.update({'total_time': test_report['total_time']})
      pipeline_details.update({'skipped_count': test_report['skipped_count']})
      pipeline_details.update({'error_count': test_report['error_count']})
      
      retval.append(pipeline_details)

    retval = retval   
    return retval

  ##########################################################

  def get_deployments(self, project_id):
    deployments = self.get_all_pages('/projects/{}/deployments?&updated_after={}'.format(project_id, self.timespan()))
    retval = [dict(deployment, **{'project_id': project_id}) for deployment in deployments]
    return retval