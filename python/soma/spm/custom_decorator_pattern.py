# -*- coding: utf-8 -*-
def checkIfArgumentTypeIsStrOrUnicode(argument_index):
  def decorator(function):
    def checkArgumentType(*args, **kwargs):
      if not (isinstance(args[argument_index], str) or isinstance(args[argument_index], unicode)):
        raise TypeError('str or unicode allowed but argument "' + str(argument_index) + '" is ' + str(type(args[argument_index])))
      else:
        pass
      return function(*args, **kwargs)
    return checkArgumentType
  return decorator

def checkIfArgumentIsInAllowedList(allowed_argument_list, argument_index):
  def decorator(function):
    def checkArgumentType(*args, **kwargs):
      if not argument_index in allowed_argument_list:
        raise ValueError("Unvalid choice : '" + str(args[argument_index]) + "' , only one of them are allowed :" + str(allowed_argument_list))
      else:
        pass
      return function(*args, **kwargs)
    return checkArgumentType
  return decorator

def checkIfArgumentTypeIsAllowed(type_allowed, argument_index):
  def decorator(function):
    def checkArgumentType(*args, **kwargs):
      if not isinstance(args[argument_index], type_allowed):
        raise TypeError(str(type_allowed) + ' allowed but argument "' + str(argument_index) + '" is ' + str(type(args[argument_index])))
      else:
        pass
      return function(*args, **kwargs)
    return checkArgumentType
  return decorator

def singleton(class_):
  instances = {}
  def getinstance(*args, **kwargs):
    if class_ not in instances:
        instances[class_] = class_(*args, **kwargs)
    return instances[class_]
  return getinstance