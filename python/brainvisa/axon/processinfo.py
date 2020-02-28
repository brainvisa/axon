
from __future__ import absolute_import
import sys
import re
from brainvisa import processes
from brainvisa.processes import ValidationError
import six


def process_description(pi, hide=[]):
    descr = ['Process ID: %s' % pi.id]
    show = ('name', 'toolbox', 'userLevel', 'valid', 'roles', 'fileName')
    trans_valid = {True: '', False: '[currently invalidated]'}
    att_transl = {'valid': ('', trans_valid)}
    hide = set(hide)

    for attrib in show:
        if attrib in hide:
            continue
        name, val_trans = att_transl.get(attrib, (attrib + ': ', None))
        value = getattr(pi, attrib)
        if val_trans:
            value = val_trans.get(value, value)
        if type(value) in (list, tuple):
            value = ', '.join(value)
        value = str(value)
        if value:
            descr.append('    %s%s' % (name, value))

    if 'short_help' not in hide:
        short_help = process_short_help(pi, indent=8, shorten_first=16,
                                        cols=80)
        if short_help:
            descr.append('    short_help: %s' % short_help)

    return '\n'.join(descr) + '\n'


def process_short_help(pi, indent=0, shorten_first=0, cols=None):
    pdoc = pi.procdoc.get(processes.neuroConfig.language,
                          pi.procdoc.get('en', {})).get('short')
    if pdoc:
        help = xhtml_to_str(pdoc, indent=indent, shorten_first=shorten_first,
                            cols=cols)
        return help
    return ''


def process_long_help(pi, indent=0, shorten_first=0, cols=None):
    pdoc = pi.procdoc.get(processes.neuroConfig.language,
                          pi.procdoc.get('en', {})).get('long')
    if pdoc:
        help = xhtml_to_str(pdoc, indent=indent, shorten_first=shorten_first,
                            cols=cols)
        return help
    return '(no description)\n'


def process_parameters_help(pi, cols=None):
    def param_type_descr(param_type):
        ti = param_type.typeInfo()
        descr = ti[0][1]
        if isinstance(param_type, processes.ReadDiskItem):
            if param_type.type is None:
                type = 'Any type'
            else:
                type = param_type.type.name
        elif isinstance(param_type, processes.ListOf):
            subtype = param_type.contentType
            descr = 'ListOf( ' + param_type_descr(subtype) + ' )'
        return descr

    pdoc = pi.procdoc.get(processes.neuroConfig.language,
                          pi.procdoc.get('en', {})).get('parameters', {})
    lines = []
    try:
        signature = processes.getProcessInstance(pi.id).signature
    except ValidationError:
        signature = processes.getProcess(
            pi.id, ignoreValidation=True).signature
    signature = list(signature.items())

    lines.append('    parameters:')
    for param, p in signature:
        ti = p.typeInfo()
        type_descr = param_type_descr(p)
        if not p.mandatory:
            type_descr += ' (optional)'
        if len(ti) > 1:
            k, access = ti[1]
        else:
            access = 'input'
        type_descr += ' (%s)' % access
        lines.append('        %s: %s' % (param, type_descr))

        descr = pdoc.get(param)
        if descr:
            doc = xhtml_to_str(descr, indent=12, cols=cols)
            if doc and doc != '\n':
                lines.append(doc)
            else:
                lines.append('')
        else:
            lines.append('')

    return '\n'.join(lines) + '\n'


def xhtml_to_str(xhtml, indent=0, shorten_first=0, cols=None):
    todo = list(xhtml.content)
    result = []
    skipped_tags = set(['img', 'style', 'head'])
    br_tags = set(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br'])
    while todo:
        item = todo.pop(0)
        if isinstance(item, six.string_types):
            result.append(item)
        else:
            if item.tag in skipped_tags:
                continue
            new_todo = item.content
            if item.tag in br_tags:
                new_todo = new_todo + ['\n']
            todo = new_todo + todo
    doc = ' '.join(result)
    return process_help_pprint(doc, indent=indent, shorten_first=shorten_first,
                               cols=cols)


def process_help_pprint(text, indent=0, shorten_first=0, cols=None):
    lines = text.split('\n')
    new_lines = []
    last_is_empty = True
    for l, line in enumerate(lines):
        line = line.strip()
        if not line:
            if not last_is_empty:
                new_lines.append('')
                last_is_empty = True
            continue
        last_is_empty = False
        if not new_lines and shorten_first:
            line = line.strip(' \t\n')
        else:
            line = ' ' * indent + line.strip(' \t\n')
        if cols:
            maxw = cols
            if not new_lines:
                maxw -= shorten_first
                if maxw <= 0:
                    new_lines.append('')
                    maxw = cols
            while len(line) > maxw:
                w = line.rfind(' ', 0, maxw)
                if w < 0:
                    w = line.find(' ')
                if w >= 0:
                    new_lines.append(line[0:w])
                    line = ' ' * indent + line[w + 1:]
                else:
                    new_lines.append(line)
                    line = ''
        if line:
            new_lines.append(line)
    return '\n'.join(new_lines) + '\n'


def filter_process(pi, proc_filters):
    for attrib, rule in proc_filters:
        value = str(getattr(pi, attrib))
        if not rule.match(value):
            return False
    return True


def process_list_help(sort_by='name', output=sys.stdout, proc_filter=None,
                      hide=None):
    proc_filters = []
    if proc_filter:
        for pf in proc_filter:
            sep = pf.find('=')
            attrib = pf[:sep]
            rule = re.compile(pf[sep + 1:])
            proc_filters.append((attrib, rule))

    proc_list = {}
    if sort_by == 'role':
        key_att = 'roles'
    else:
        key_att = sort_by
    for pi in processes.allProcessesInfo():
        processes.readProcdoc(pi.id)  # ensure doc is here
        if proc_filter and not filter_process(pi, proc_filters):
            continue
        keys = getattr(pi, key_att)
        if type(keys) not in (list, tuple):
            keys = (keys,)
        for key in keys:
            plentry = proc_list.setdefault(key, {})
            plentry[pi.id] = process_description(pi, hide)

    sorted_entries = sorted(proc_list.keys())
    descr_list = []
    for key in sorted_entries:
        entry = proc_list[key]
        ids = sorted(entry.keys())
        for pid in ids:
            descr_list.append(entry[pid])

    output.write('\n'.join(descr_list))


def process_help(process, output=sys.stdout, html=False, cols=80):
    pi = processes.getProcessInfo(process)
    processes.readProcdoc(pi.id)  # ensure doc is here
    descr = process_description(pi)
    param_help = process_parameters_help(pi, cols=cols)
    long_help = process_long_help(pi, indent=8, shorten_first=17, cols=cols)
    descr += '%s    description: %s' % (param_help, long_help)

    output.write(descr)
