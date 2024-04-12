#ifndef __SPIDER_MONKEY_PYTHON__
#define __SPIDER_MONKEY_PYTHON__

#include <map>
#include <jsapi.h>
#include "smjs.h"

typedef PyObject* (*jsconv_t)(JSContext* ctx, const JS::MutableHandleValue& value);

jsconv_t* smjs_getconvertors(JSContext* ctx, JS::CallArgs& args);
PyObject* smjs_convert(JSContext* ctx, JS::CallArgs& args, jsconv_t* converters);
PyObject* smjs_convertsingle(JSContext* ctx, const JS::MutableHandleValue& value);
bool smjs_convertresult(JSContext* ctx, JS::CallArgs& args, PyObject* pobj);

class SMPythonContext
{
public:
  SMContext* sm;
  JSClass* proxycls;
  std::map<JSFunction*, std::string> getters;
  std::map<JSFunction*, std::string> setters;
public:
  SMPythonContext(SMContext* _sm) { sm = _sm; proxycls = NULL; }
  virtual ~SMPythonContext() {}
};

#endif
