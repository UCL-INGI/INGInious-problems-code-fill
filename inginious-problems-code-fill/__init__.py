# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
import re
import web
import json
import gettext
import itertools

from inginious.common.tasks_problems import CodeProblem
from inginious.frontend.task_problems import DisplayableCodeProblem
from inginious.frontend.parsable_text import ParsableText


__version__ = "0.1"

def normalize(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')

class CodeFillProblem(CodeProblem):
    """
    Fill-in-the-blanks code problem
    """
    def __init__(self, task, problem_id, content):
        super().__init__(task, problem_id, content)
        self._default = normalize(self._default)

    @classmethod
    def get_type(cls):
        return "code_fill"

    @classmethod
    def parse_problem(cls, problem_content):
        return problem_content

    @classmethod
    def problem_type(self):
        return dict

    def getFillRegex(self):
        regex = r'({})'.format(re.sub(r'\\{%.+?%\\}', r')\{%(.*?)%\}(', re.escape(self._default), flags=re.DOTALL))
        return re.compile(regex, flags=re.DOTALL)

    def input_is_consistent(self, task_input, default_allowed_extension, default_max_size):
        if not str(self.get_id()) in task_input:
            return False
        return task_input[self.get_id()]["matches"]

class DisplayableCodeFillProblem(CodeFillProblem, DisplayableCodeProblem):

    """ A displayable fill-in-the-blanks code problem """
    def __init__(self, problemid, content, translations, taskfs):
        super(DisplayableCodeFillProblem, self).__init__(problemid, content, translations, taskfs)

    @classmethod
    def get_type_name(self, gettext):
        return "code-fill"

    @classmethod
    def get_renderer(cls, template_helper):
        """ Get the renderer for this class problem """
        return template_helper.get_custom_renderer(os.path.join(PATH_TO_PLUGIN, "templates"), False)

    def show_input(self, template_helper, language, seed):
        """ Show BasicCodeProblem and derivatives """
        header = ParsableText(self.gettext(language, self._header), "rst",
                              translation=self.get_translation_obj(language))
        return str(DisplayableCodeFillProblem.get_renderer(template_helper)
                   .tasks.code_fill(self.get_id(), header, 8, 0, self._language, self._optional, self._default))

    #@classmethod
    #def show_editbox(cls, template_helper, key, language):
    #    return DisplayableCodeFillProblem.get_renderer(template_helper).course_admin.subproblems.code(key, False)

    def adapt_input_for_backend(self, input_data):
        """ Adapt the input from web.py for the inginious.backend """
        if not str(self.get_id()) in input_data:
            return input_data

        text = normalize(input_data[self.get_id()])
        match = self.getFillRegex().fullmatch(text)
        if not match:
            input_data[self.get_id()] = { "input": text,
                                          "template": self._default,
                                          "matches": False, }
            return input_data

        template = "".join(t.format(s) for (s, t) in zip(match.groups(), itertools.cycle(("{}", "{{%{}%}}"))))
        input_data[self.get_id()] = { "input": text,
                                      "template": self._default,
                                      "code": ''.join(match.groups()),
                                      "regions": match.groups()[1::2],
                                      "matches": True, }
        return input_data




PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))

class StaticMockPage(object):
    # TODO: Replace by shared static middleware and let webserver serve the files
    def GET(self, path):
        if not os.path.abspath(PATH_TO_PLUGIN) in os.path.abspath(os.path.join(PATH_TO_PLUGIN, path)):
            raise web.notfound()

        try:
            with open(os.path.join(PATH_TO_PLUGIN, "static", path), 'rb') as file:
                return file.read()
        except:
            raise web.notfound()

    def POST(self, path):
        return self.GET(path)

def init(plugin_manager, course_factory, client, plugin_config):
    # TODO: Replace by shared static middleware and let webserver serve the files
    plugin_manager.add_page('/plugins/code-fill/static/(.+)', StaticMockPage)
    plugin_manager.add_hook("css", lambda: "/plugins/code-fill/static/css/code-fill.css")
    plugin_manager.add_hook("javascript_header", lambda: "/plugins/code-fill/static/js/code-fill.js")
    course_factory.get_task_factory().add_problem_type(DisplayableCodeFillProblem)
