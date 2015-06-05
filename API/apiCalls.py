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

from Model.Project import Project
from Model.Sample import Sample
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

    if validateURLForm(baseURL):
        oauth_service=get_oauth_service(baseURL)
        access_token=get_access_token(oauth_service, username, password)
        session=oauth_service.get_session(access_token)
    else:
        raise URLError(vRes.getErrors())

    return session


def validateURLexistance(url, session=None):
    """
    tries to validate existance of given url by trying to open it.
    true if HTTP OK, false if HTTP NOT FOUND otherwise raises error containing error code and message

    arguments:
        url -- the url link to open and validate

    returns
        true if http response OK 200
        false if http response NOT FOUND 404
    """

    if session!=None:
        response=session.get(url)

        if response.status_code==httplib.OK:
            return True
        elif response.status_code==httplib.NOT_FOUND:
            return False
        else:
            raise Exception( str(response.status_code) + response.reason)

    else:
        response = urlopen(url, timeout=MAX_TIMEOUT_WAIT)

        if response.code==httplib.OK:
            return True
        elif response.code==httplib.NOT_FOUND:
            return False
        else:
            raise Exception( str(response.code) + response.msg)


def get_oauth_service(baseURL):
    """
    get oauth service to be used to get access token

    argument:
        baseURL -- URL of IRIDA server API

    returns oauthService
    """

    accessTokenUrl = baseURL + "oauth/token"

    oauth_serv = OAuth2Service(
    client_id=clientId,
    client_secret=clientSecret,
    name="irida",
    access_token_url = accessTokenUrl,
    base_url=baseURL)



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


def getLink(session, baseURL, targetKey, targID=""):
    """
    makes a call to baseURL(api) expecting a json response
    tries to retrieve targetKey from response to find link to that resource

    arguments:
        session -- opened OAuth2Session
        baseURL -- URL to retrieve link from
        targetKey -- name of link (e.g projects or project/samples)
        targID -- optional id to search for in targets. will try to match with key 'identifier'

    returns link if it exists

    """
    retVal=None


    if validateURLexistance(baseURL, session):
        response=session.get(baseURL)


        linksList=response.json()["resource"]["links"]
        for link in linksList:

            if link["rel"]==(targetKey):
                retVal=link["href"]
                break
        else:
            raise KeyError(targetKey+" not found in links. "+ "Available links: " + ",".join([ str(link["rel"]) for link in linksList])[:-1] )


    else:
        raise request_HTTPError("Error: " + url +" is not a valid URL")

    return retVal

def getProjects(session, baseURL):
    """
    API call to api/projects to get list of projects

    arguments:
        session -- opened OAuth2Session
        baseURL -- URL of IRIDA server API

    returns list containing projects. each project is a dictionary.
    """

    projectList=[]

    url=getLink(session, baseURL, "projects")


    if validateURLexistance(url, session):
        response = session.get(url)

        result= response.json()["resource"]["resources"]
        for projDict in result:
            projectList.append( Project(projDict["identifier"],projDict["name"], projDict["projectDescription"]) )

    else:
        raise request_HTTPError("Error: " + url +" is not a valid URL")

    return projectList


def getSamples(session, baseURL, project):
    """
    API call to api/projects/projectID/samples

    arguments:
        session -- opened OAuth2Session
        baseURL -- URL of IRIDA server API
        project -- a Project object

    returns list of samples for the given project. each sample is a Sample object.
    """

    sampleList=[]


    projectID=project.getID()
    projUrl=getLink(session, baseURL, "projects")+"/"+projectID
    url=getLink(session, projUrl, "project/samples")

    if validateURLexistance(url, session):

        response = session.get(url)
        result = response.json()["resource"]["resources"]
        for sampleDict in result:
            sampleList.append( Sample(sampleDict) )

	else:
		raise request_HTTPError("The given project ID doesn't exist")

    return sampleList


def does_projectID_exist(session,projectID):
    retVal=False
    projectsList=getProjects(session)

    for project in projectsList:
        if project.getID()==projectID:
            retVal=True
            break

    return retVal

def does_sampleID_exist(session,projectID,sampleID):
    retVal=False
    samplesList=getSamples(session,projectID)

    for sample in samplesList:
        if sample.getID()==sampleID:
            retVal=True
            break

    return retVal

def getSequenceFiles(session, baseURL, projectID, sampleID):
    """
    API call to api/projects/projectID/sampleID/sequenceFiles

    arguments:
        session -- opened OAuth2Session
        baseURL -- URL of IRIDA server API
        projectID -- project ID/ 'identifier' which is just a number
        sampleID -- sample ID for given project ID- number string


    returns list of sequenceFiles for given sampleID
    """

    projUrl=getLink(session, baseURL, "projects")+"/"+projectID
    sampleUrl=getLink(session, projUrl, "project/samples")+"/"+sampleID
    url=getLink(session, sampleUrl, "sample/sequenceFiles")

    response = session.get(url)

    if response.status_code==httplib.OK:
        result = response.json()["resource"]["resources"]

    elif response.status_code==httplib.NOT_FOUND:
        if does_projectID_exist(session, projectID)==False:
            raise request_HTTPError("The given project ID doesn't exist")
        else:
            raise request_HTTPError("The given sample ID doesn't exist")

    else:
        raise request_HTTPError("Error: "+ str(response.status_code)+ " " + response.reason)

    return result


def sendProjects(session, baseURL, projectDict):
    """
    post request to send a project to IRIDA via API
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
        url=getLink(session, baseURL, "projects")
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

def sendSamples(session, baseURL, projectID, samplesList):
    """
    post request to send sample(s) to the project of given projectID

    arguments:
        session -- opened OAuth2Session
        baseURL -- URL of IRIDA server API
        projectID -- string # identifier for the given project in IRIDA
        samplesList -- list containing Sample object(s) to send
    """

    jsonRes=None

    #validateSamples

    projUrl=getLink(session, baseURL, "projects")+"/"+projectID
    url=getLink(session, projUrl, "project/samples")
    print url
    headers = {'headers': {'Content-Type':'application/json'}}

    for sample in samplesList:
        jsonObj=json.dumps(sample.getDict())
        print jsonObj
        response =session.post(url, jsonObj, **headers)

        if response.status_code==httplib.CREATED:#201
            jsonRes= json.loads(response.text)
        else:
            raise ProjectError("Error: " + str(response.status_code) + " "+ response.text)
