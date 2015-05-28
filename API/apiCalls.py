import ast
import json
import httplib

import sys
sys.path.append("../")

from requests import Request
from requests.exceptions import HTTPError
from urllib2 import Request, urlopen, URLError
from urlparse import urlparse

from rauth import OAuth2Service

from Model.ValidationResult import ValidationResult
from Exceptions.ProjectError import ProjectError


clientId="testClient"
clientSecret="testClientSecret"

MAX_TIMEOUT_WAIT=30


def createSession(baseURL, username, password):

    vRes=validateURL(baseURL)
    if vRes.isValid():
        oauth_service=get_oauth_service(baseURL)
        access_token=get_access_token(oauth_service, username, password)
        session=oauth_service.get_session(access_token)
    else:
        raise URLError(vRes.getErrors())

    return session

def validateURL(url, session=None):
    #move later to Validation/onlineValidation.py ?

    vRes=ValidationResult()


    try:
        if session==None:
            response = urlopen(url)
        else:
            response=session.get(url)

    except URLError, e:

        if e.code!=UNAUTHORIZED:
            msg="Failed to reach " + url +"\n"
            if hasattr(e, 'reason'):
                if len(str(e.reason))>0:
                    msg= msg + str(e.reason)
                vRes.addErrorMsg( msg )
            else:
                msg=msg + 'Error code: ' + e.code
                vRes.addErrorMsg( msg)

            valid=False

    except ValueError, e:

        parsed=urlparse(url)
        if len(parsed.scheme)==0:
            vRes.addErrorMsg("URL must include scheme. (e.g http://, https://)")
        else:
            vRes.addErrorMsg("The URL enterred is formed incorrectly. ")
        valid=False

    else:
        valid=True

    vRes.setValid(valid)

    return vRes

def get_oauth_service(baseURL):
    """
        get oauth service to be used to get access token
        checks if baseURL is valid and checks if baseURL/oauth/token is also valid.
        accessTokenUrl = baseURL + "oauth/token"
        Raises Exception if either baseURL or accessTokenUrl is not valid AND it's error messages DOESN'T contain "Unauthorized"- expecting to get "Unauthorized" when validating. This is so that we still raise an error if the either URL is malformed(baseURL could be missing '/' at the end ) or even if baseURL is valid, it may not have a oauth/token path.

        argument:
            baseURL -- URL of IRIDA server API

        returns oauthService
    """

    accessTokenUrl = baseURL + "oauth/token"
    vRes=validateURL(accessTokenUrl)
    print accessTokenUrl
    if vRes.isValid() or "Unauthorized" in vRes.getErrors() :
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


def getProjects(session, baseURL):
    """
        API call to api/projects to get list of projects

        arguments:
            session -- opened OAuth2Session

        returns list containing projects. each project is a dictionary.
    """

    result=None

    url=baseURL+"projects"
    vRes=validateURL(url, session)

    if vRes.isValid():

        response = session.get(url)
        #getProjects.response=response
        result = response.json()["resource"]["resources"]
    else:
        print vRes.getErrors()
    return result


def getSamples(session, projectID):
    """
        API call to api/projects/projectID/samples

        arguments:
            session -- opened OAuth2Session
            projectID -- project ID/ 'identifier' which is just a number

        returns list of samples for the given projectID. each sample is a dictionary
    """

    url=baseURL+"projects/"+projectID+"/samples"
    response = session.get(url)
    if response.status_code==httplib.OK:
        result = response.json()["resource"]["resources"]

    elif response.status_code==httplib.NOT_FOUND:
        raise HTTPError("The given project ID doesn't exist")

    else:
        raise HTTPError("Error: "+response.status_code+ " " + response.reason)

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

def getSequenceFiles(session, projectID, sampleID):
    """
        API call to api/projects/projectID/sampleID/sequenceFiles

        arguments:
            session -- opened OAuth2Session
            projectID -- project ID/ 'identifier' which is just a number

        returns list of sequenceFiles for given sampleID
    """

    url=baseURL+"projects/"+projectID+"/samples/"+sampleID+"/sequenceFiles"

    response = session.get(url)

    if response.status_code==httplib.OK:
        result = response.json()["resource"]["resources"]

    elif response.status_code==httplib.NOT_FOUND:
        if does_projectID_exist(session, projectID)==False:
            raise HTTPError("The given project ID doesn't exist")
        else:
            raise HTTPError("The given sample ID doesn't exist")

    else:
        raise HTTPError("Error: "+response.status_code+ " " + response.reason)

    return result


def sendProjects(session, projectDict):
    #validate projectDict

    #{"name":["You must provide a project name."],"label":["You must provide a label."]} - label?

    if projectDict.has_key("name"):
        url=baseURL+"projects"
        jsonObj=json.dumps(projectDict)
        headers = {'headers': {'Content-Type':'application/json'}}

        response =session.post(url,jsonObj, **headers)

        if response.status_code==httplib.CREATED:
            print response.text
        else:
            raise ProjectError("Error: " + str(response.status_code) + " "+ response.text)

    else:
        raise ProjectError("Missing project name. A project requires 'name' as one of its keys")



def sendSequenceFile(session, projectID, sampleID, pfList):
    url=baseURL+"projects/"+projectID+"/samples/"+sampleID+"/sequenceFiles"

    headers = {'headers': {'Content-Type':'application/json'}}



#temp- will become data taken from user input
if __name__=="__main__":
    baseURL="http://localhost:8080/api/"
    username="admin"
    password="password1"

    session=createSession(baseURL, username, password)
    projectsList=getProjects(session,baseURL)
    print len(projectsList)
    print projectsList[0]
