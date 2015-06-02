import ast
import json
import httplib

import sys
sys.path.append("../")

from os import path
from requests import Request
from requests.exceptions import HTTPError as request_HTTPError
from urllib2 import Request, urlopen, URLError, HTTPError

from rauth import OAuth2Service, OAuth2Session

from Model.ValidationResult import ValidationResult
from Exceptions.ProjectError import ProjectError
from Validation.offlineValidation import validateURLForm
from ConfigParser import RawConfigParser


pathToModule=path.dirname(__file__)
if len(pathToModule)==0:
	pathToModule='.'

confParser=RawConfigParser()
confParser.read(pathToModule+"/../config.conf")

clientId=confParser.get("apiCalls","clientId")
clientSecret=confParser.get("apiCalls","clientSecret")

MAX_TIMEOUT_WAIT=int(confParser.get("apiCalls","maxWaitTime"))


def createSession(baseURL, username, password):
    """
    create session to be re-used for get and post calls
    arguments:
        baseURL -- url of the IRIDA server
        username -- username for server
        password -- password for given username

    returns session (OAuth2Session object)
    """
    vRes=validateURLForm(baseURL)
    if vRes.isValid():
        oauth_service=get_oauth_service(baseURL)
        access_token=get_access_token(oauth_service, username, password)
        session=oauth_service.get_session(access_token)
    else:
        raise URLError(vRes.getErrors())

    return session

def validateURLexistance(url):
    """
    tries to validate existance of given url by trying to open it.
    the passed url are assumed to have passed validation via validateURLForm
    expecting to receive status_code 401/UNAUTHORIZED when trying to validate baseURL/api

    arguments:
        url -- the url link to open and validate

    returns ValidationResult object - stores bool valid and list of string error messages
    """

    #move later to Validation/onlineValidation.py ?


    vRes=ValidationResult()
    valid=True

    try:
        response = urlopen(url, timeout=MAX_TIMEOUT_WAIT)

    except HTTPError, e:

        if hasattr(e,'code'):
            if e.code!=httplib.OK and e.code!=httplib.UNAUTHORIZED :
                msg="Failed to reach " + url +"\n"
                msg=msg + 'Error code: ' + str(e.code)
                valid=False


                if hasattr(e, 'reason'):
                    if len(str(e.reason))>0:
                        msg= msg + ". " + str(e.reason)

                vRes.addErrorMsg( msg )

        else:
            msg="Failed to reach " + url +"\n"
            vRes.addErrorMsg( msg )
            valid=False

    vRes.setValid(valid)

    return vRes

def get_oauth_service(baseURL):
    """
    get oauth service to be used to get access token
    checks if baseURL is valid and checks if baseURL/oauth/token is also valid.
    accessTokenUrl = baseURL + "oauth/token"
    Raises request_HTTPError if accessTokenUrl is invalid.

    argument:
        baseURL -- URL of IRIDA server API

    returns oauthService
    """

    accessTokenUrl = baseURL + "oauth/token"

    vRes=validateURLexistance(accessTokenUrl)
    if vRes.isValid():
        oauth_serv = OAuth2Service(
        client_id=clientId,
        client_secret=clientSecret,
        name="irida",
        access_token_url = accessTokenUrl,
        base_url=baseURL)

    else:
        raise request_HTTPError(vRes.getErrors())

    return oauth_serv

def get_access_token(oauth_service, username, password):
    """
    get access token to be used to get session from oauth_service

    arguments:
        oauth_service -- O2AuthService from get_oauth_service
        username -- username for IRIDA
        password -- password for given IRIDA username

    returns access token
    """

    params = {'data' : {'grant_type' : 'password',
        'client_id' : clientId,
        'client_secret' : clientSecret,
        'username' : username,
        'password' : password}}

    access_token =    oauth_service.get_access_token(decoder=decoder,**params)

    return access_token

def decoder(return_dict):
    """
        safely parse given dictionary

        arguments:
            return_dict -- access token dictionary

        returns evaluated dictionary
    """

    irida_dict = ast.literal_eval(return_dict)
    return irida_dict


def getProjects(session, baseURL):
    """
    API call to api/projects to get list of projects

    arguments:
        session -- opened OAuth2Session
        baseURL -- URL of IRIDA server API

    returns list containing projects. each project is a dictionary.
    """

    result=None

    url=baseURL+"projects"

    response = session.get(url)
    if response.status_code==httplib.OK:
        try:
            result = response.json()["resource"]["resources"]
        except KeyError, e:
            raise KeyError("Error:" + str(response.status_code) + " " + response.reason)
    else:
        raise request_HTTPError("Error: "+ str(response.status_code)+ " " + response.reason)

    return result


def getSamples(session, projectID, baseURL):
    """
    API call to api/projects/projectID/samples

    arguments:
        session -- opened OAuth2Session
        projectID -- project ID/ 'identifier' which is just a number string
        baseURL -- URL of IRIDA server API

    returns list of samples for the given projectID. each sample is a dictionary
    """

    url=baseURL+"projects/"+projectID+"/samples"
    response = session.get(url)
    if response.status_code==httplib.OK:
        result = response.json()["resource"]["resources"]

    elif response.status_code==httplib.NOT_FOUND:
        raise request_HTTPError("The given project ID doesn't exist")

    else:
        raise request_HTTPError("Error: "+ str(response.status_code)+ " " + response.reason)

    return result


def does_projectID_exist(session,projectID):
    retVal=False
    projectsList=getProjects(session)

    for project in projectsList:
        if project['identifier']==projectID:
            retVal=True
            break

    return retVal

def does_sampleID_exist(session,projectID,sampleID):
    retVal=False
    samplesList=getSamples(session,projectID)

    for sample in samplesList:
        if sample['identifier']==sampleID:
            retVal=True
            break

    return retVal

def getSequenceFiles(session, projectID, sampleID, baseURL):
    """
    API call to api/projects/projectID/sampleID/sequenceFiles

    arguments:
        session -- opened OAuth2Session
        projectID -- project ID/ 'identifier' which is just a number
        sampleID -- sample ID for given project ID- number string
        baseURL -- URL of IRIDA server API

    returns list of sequenceFiles for given sampleID
    """

    url=baseURL+"projects/"+projectID+"/samples/"+sampleID+"/sequenceFiles"

    response = session.get(url)

    if response.status_code==httplib.OK:
        result = response.json()["resource"]["resources"]

    elif response.status_code==httplib.NOT_FOUND:
        if does_projectID_exist(session, projectID)==False:
            raise request_HTTPError("The given project ID doesn't exist")
        else:
            raise request_HTTPError("The given sample ID doesn't exist")

    else:
        raise request_HTTPError("Error: "+response.status_code+ " " + response.reason)

    return result


def sendProjects(session, projectDict, baseURL):
    """
    post request to send a project to irida via API
    the project being sent requires a name

    arguments:
        session -- opened OAuth2Session
        projectDict -- a dictionary of the project to be sent. requires a name key. projectDescription key is optional.
        baseURL -- URL of IRIDA server API

    returns a dictionary containing the result of post request. when post is successful the dictionary it returns will contain the same name and projectDescription that was originally sent as well as additional keys like createdDate and identifier.
    when post fails then an error will be raised so return statement is not even reached.
    """
    #validate projectDict?

    jsonRes=None
    if projectDict.has_key("name"):#add 'and' condition for "name must be 5 char long" here?
        url=baseURL+"projects"
        jsonObj=json.dumps(projectDict)
        headers = {'headers': {'Content-Type':'application/json'}}

        response =session.post(url,jsonObj, **headers)

        if response.status_code==httplib.CREATED:#201
            jsonRes= json.loads(response.text)
        else:
            raise ProjectError("Error: " + str(response.status_code) + " "+ response.text)

    else:
        raise ProjectError("Missing project name. A project requires 'name' as one of its keys")

    return jsonRes



#just for your testing - will be removed before merge to develop
if __name__=="__main__":
    #temp- will become data taken from user input
    baseURL="http://localhost:8080/api/"
    username="admin"
    password="password1"

    session=createSession(baseURL, username, password)

    projectsList=getProjects(session,baseURL)
    print "\n# of projects:", len(projectsList)

    print sendProjects(session , {"name":"projectX"}, baseURL)

    projectsList=getProjects(session,baseURL)
    print "\n# of projects:", len(projectsList)
    print "Added project:", projectsList[len(projectsList)-1]
