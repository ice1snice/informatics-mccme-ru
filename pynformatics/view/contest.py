from pyramid.view import view_config
from pynformatics.model import User, EjudgeContest, Run, Comment, EjudgeProblem, Problem
from pynformatics.contest.ejudge.serve_internal import EjudgeContestCfg
from pynformatics.contest.ejudge.serve_internal import *
from pynformatics.contest.ejudge.configparser import ConfigParser
from pynformatics.view.utils import *
import sys, traceback, collections
#import jsonpickle, demjson
from phpserialize import *
from pynformatics.view.utils import *
from pynformatics.utils.problemParser import getCorrectTree
from pynformatics.models import DBSession
import transaction
#import jsonpickle, demjson
import json
from pynformatics.models import DBSession
#from webhelpers.html import *
from xml.etree.ElementTree import ElementTree
import zipfile
import re
import os
import xml.etree.ElementTree as ET



HOME_JUDGES = '/home/judges/'

def get_contest_path(number):
    return HOME_JUDGES + '0'*(6-len(str(number))) + str(number) + '/'

def get_contest_path_conf(number):
    return get_contest_path(number) + 'conf/'

def get_problem_dir(contest_id, problem_internal_name):
    return get_contest_path(contest_id) + 'problems/' + problem_internal_name + '/'
        
def get_problem_archive_name(contest_id, problem_internal_name, revision):
    return get_contest_path(contest_id) + 'download/' + problem_internal_name + '-' + revision + '$linux.zip'

def replImg(m):
    return '<IMG' + m.group(1) + '/>' 

def makehash():
    return collections.defaultdict(makehash)

def checkCapability(request):
    if (not RequestCheckUserCapability(request, 'moodle/ejudge_contests:reload')):
        raise Exception("Auth Error")

def getOrCreateContest(request, ejudge_contest_id):
    strId = getContestStrId(ejudge_contest_id);
    ejudgeCfg = EjudgeContestCfg("/home/judges/" + strId + "/conf/serve.cfg");
    contest = DBSession.query(EjudgeContest).filter(EjudgeContest.ejudge_int_id == ejudge_contest_id).first()
        
    tree = ElementTree()
    tree.parse("/home/judges/data/contests/" + strId + ".xml")
    contestName = tree.find("name").text
        
    if (contest == None):
        contest = EjudgeContest(contestName, request.matchdict['contest_id']);
        with transaction.manager:
            DBSession.add(contest);
    return [contest, ejudgeCfg]
    
def updateStatement(problem, p, contest, conf):
    use_in_statement = ""
    flag = ""
    if (conf.config.has_option("default", 0, "advanced_layout")):
        if conf.config.get("default", 0, "advanced_layout") == None:
            problem_local_config = ConfigParser(allow_no_value = True, strict = False, interpolation = None)
            problem_local_config.read(get_problem_dir(contest.ejudge_int_id, p.internal_name) + 'problem.cfg')
            
            try:
                extid = problem_local_config.get("problem", 0, "extid")[0].strip("\"")
            except:
                extid = ""
                
            if "polygon" in extid:
                revision = problem_local_config.get("problem", 0, "revision")[0].strip("\"")
                try:
                    tttt = "@" + revision
                    with zipfile.ZipFile(get_problem_archive_name(contest.ejudge_int_id, p.internal_name, revision)) as arch:
                        xml_description = arch.read("problem.xml")
                        xml_description = ET.fromstring(xml_description)
                        
                        use_in_statement = ""
                        test_num = 0
                        
                        for test_node in xml_description.findall(".//testset/tests/test"):
                            test_num += 1
                            try:
                                if test_node.attrib['sample'] == 'true':
                                    if use_in_statement != "":
                                        use_in_statement += ','
                                    use_in_statement += str(test_num)
                            except Exception as e:
                                tttt += str(e)
                                pass
                        
                        res = arch.read("statements/.html/russian/problem.html")
                        
#                        res = re.sub('<META[^>]*>', '', res.decode("utf-8"))
#                        res = re.sub('<LINK[^>]*>', '', res)
#                        res = re.sub('<BR>', '<BR/>', res)
#                        res = re.sub('&nbsp;', '&#160;', res)
#                        res = re.sub('&mdash;', '&#8212;', res)
#                        res = re.sub('&ndash;', '&#150;', res)
#                        res = re.sub('&raquo;', '&#187;', res)
#                        res = re.sub('&laquo;', '&#171;', res)
#                        res = re.sub('&middot;', '&#183;', res)
#                        res = re.sub('&ldquo;', '&#8220;', res)
#                        res = re.sub('&rdquo;', '&#8221;', res)
#                        res = re.sub('&lsquo;', '&#8216;', res)
#                        res = re.sub('&rsquo;', '&#8217;', res)
#                        res = re.sub('&times;', '&#215;', res)
#                        res = re.sub('&thinsp;', '&#8201;', res)
#                        res = re.sub('&lt;', '&#8804;', res)
#                        res = re.sub('&ne;', '&#8800;', res)
#                        res = re.sub('&le;', '&#8804;', res)
#                        res = re.sub('&ge;', '&#8805;', res)
#                        res = re.sub('<IMG([^>]*)>', replImg, res)
                        try:
                            tree = ET.fromstring(getCorrectTree(res))
                        except:
                            return "Parse Error"

                        for statement_node in tree.findall(".//div[@class='problem-statement']"):
                            for n in statement_node.findall(".//div[@class='header']"):
                                statement_node.remove(n)
                            if True or use_in_statement != "":
                                flag = "---"
                                for n in statement_node.findall(".//div[@class='sample-tests']"):
                                    statement_node.remove(n)
                            try:
                                os.mkdir("/var/www/moodle_probpics/" + str(problem.id));
                            except OSError:
                                pass
                            for img in statement_node.findall(".//img[@class='tex-graphics']"):
                                file_name = img.attrib["src"]
                                try:
                                    with open("/var/www/moodle_probpics/" + str(problem.id) + "/" + file_name, "wb") as f:
                                        f.write(arch.read("statements/.html/russian/" + file_name))
                                    img.attrib["src"] = "http://informatics.mccme.ru/moodle_probpics/" + str(problem.id)+ "/" + file_name
                                except:
                                    pass
                                    
                            for img in statement_node.findall(".//img[@class='tex-formula']"):
                                file_name = img.attrib["src"]
                                try:
                                    with open("/var/www/moodle_probpics/" + str(problem.id) + "/" + file_name, "wb") as f:
                                        f.write(arch.read("statements/.html/russian/" + file_name))
                                    img.attrib["src"] = "http://informatics.mccme.ru/moodle_probpics/" + str(problem.id)+ "/" + file_name
                                except:
                                    pass

                            problem.content = ET.tostring(statement_node, encoding = 'utf-8').decode("utf-8")
                        problem.sample_tests = use_in_statement
                except KeyError:
                    pass   
    problem.sample_tests = use_in_statement
    problem.generateSamples()
    return "OK" + flag + use_in_statement
    
def updateOrAddProblem(problem_id, contest, ejudgeCfg, update_statement = False):    
    problem = DBSession.query(EjudgeProblem).filter(EjudgeProblem.contest_id == contest.id).filter(EjudgeProblem.problem_id == problem_id).first()
    problemCfg = ejudgeCfg.getProblem(problem_id)
    if problem == None:
        problem = EjudgeProblem(problemCfg.long_name, problemCfg.time_limit, problemCfg.memory_limit, problemCfg.output_only, contest.id, problem_id, problemCfg.short_name, contest.ejudge_int_id, "<p>Условие пока не опубликовано...</p>")
        with transaction.manager:
            DBSession.add(problem)
        transaction.commit()
        action = "add"
        content = ""
    else:
        session = DBSession()
        problem.ejudge_name = "" + problemCfg.long_name
#        if problem.name == "":
        problem.name = "" + problemCfg.long_name
        problem.timelimit = problemCfg.time_limit 
        problem.memorylimit = problemCfg.memory_limit
        problem.output_only = problemCfg.output_only
        problem.short_id = problemCfg.short_name
        if update_statement:
            content = updateStatement(problem, problemCfg, contest, ejudgeCfg)
        session.flush()
        
        #session.commit()
        transaction.commit()
    #    DBSession.commit() 
        action = "edit"   
        
    return [problem, problemCfg, action, content]
    
        
@view_config(route_name='contest.ejudge.reload.problem', renderer='string')
def reload_problem(request):
    try:
        checkCapability(request)
        contest, ejudgeCfg = getOrCreateContest(request, request.matchdict['contest_id'])
        
        problem, problemCfg, action, content = updateOrAddProblem(request.matchdict['problem_id'], contest, ejudgeCfg, True)

#        jsonpickle.set_preferred_backend('demjson')   
        res = {"action": action, "a1": problem.ejudge_prid , "problem": problem, "contest_id" : request.matchdict['contest_id'], "problemCount" : ejudgeCfg.getProblemsCount(), "abstractProblemCount" : ejudgeCfg.getAbstractProblemsCount(), "problem" : ejudgeCfg.getProblem(request.matchdict['problem_id']).getInfo()}
        return json.dumps(res)
    except Exception as e: 
        return {"result" : "error", "message" : e.__str__(), "stack" : traceback.format_exc()}

@view_config(route_name='contest.ejudge.reload', renderer='json')
def reload_contest(request):
    try:
        checkCapability(request)
        contest, ejudgeCfg = getOrCreateContest(request, request.matchdict['contest_id'])
        
        actions = []
        
        for pr_id in ejudgeCfg.problems:  
            try:
                problem, problemCfg, action, content = updateOrAddProblem(pr_id, contest, ejudgeCfg, True)
                actions.append([content, action, problem.name, pr_id, problem.short_id, problem.problem_id, problem.id, problem.ejudge_prid])
            except Exception as e:
               return {"pr_id": pr_id, "result" : "error", "message" : e.__str__(), "stack" : traceback.format_exc()}
#        jsonpickle.set_preferred_backend('demjson')   
        res = {"action": actions, "name": contest.name, "contest_id" : request.matchdict['contest_id'], "problemCount" : ejudgeCfg.getProblemsCount(), "abstractProblemCount" : ejudgeCfg.getAbstractProblemsCount()}
        return res
    except Exception as e: 
        return {"result" : "error", "message" : e.__str__(), "stack" : traceback.format_exc()}

@view_config(route_name='contest.ejudge.get_table', renderer='pynformatics:templates/language_table.mak')    
def get_table(request):
    try:
        checkCapability(request)
        
        columns = dict()
        header = '<tr><td>contest</td>'
        contests = dict()
        i = 1

        langs = []
        options = []
        
        for contest_id in sorted(all_contests()):
            cfg_file = HOME_JUDGES + contest_id + '/conf/serve.cfg'
            try:
                contest = EjudgeContestCfg(cfg_file)
            except IOError:
                pass
            except UnicodeDecodeError:
                print(cfg_file)
            except KeyError:
                print(cfg_file)
            section = 'language'
                
            for i in range(contest.config.get_sections_count(section)):
                cur_options = contest.config.options(section, i)
                cur_id =  contest.config.get(section, i, 'id')[0]
                if cur_id not in langs:
                    langs += [cur_id]
                for opt in cur_options:
                    if opt not in options:
                        options += [opt]
            
        res = collections.defaultdict(lambda : collections.defaultdict(dict))

        strr = ""
        
        for contest_id in sorted(all_contests()):
            cfg_file = HOME_JUDGES + contest_id + '/conf/serve.cfg'
            try:
                contest = EjudgeContestCfg(cfg_file)
            except IOError:
                pass
            except UnicodeDecodeError:
                print(cfg_file)
            except KeyError:
                print(cfg_file)
            section = 'language'
            
            for l in langs:
                for opt in options:
                    res[l][opt][contest_id] = ''
            
            for i in range(contest.config.get_sections_count(section)):
                cur_id =  contest.config.get(section, i, 'id')[0]
                for opt in options:
                    r = contest.config.get(section, i, opt, raw = True, fallback = '-')
                    if r != None:
                        res[cur_id][opt][contest_id] = ",".join(r)
                    if res[cur_id][opt][contest_id] == '':
                        res[cur_id][opt][contest_id] = "+"
                    if res[cur_id][opt][contest_id] == '-':
                        res[cur_id][opt][contest_id] = ""            
        return { "tmp":strr, "result" : res, "status": True, "langs" : langs, "options" : options, "contests" : sorted(all_contests())}
    except Exception as e: 
        return {"status": False, "result" : "error", "message" : e.__str__(), "stack" : traceback.format_exc()}
