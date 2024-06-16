#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <iostream>
#include <format>
#include "smjspython.h"
#include <js/CompilationAndEvaluation.h>
#include <js/Conversions.h>
#include <js/Object.h>

static bool smjsinit = false;

// attribute of Python context with reference to a SMPythonConext
static const char* smattrname = "sm";

// attribute of Python context with reference to a global object
static const char* globalattrname = "globj";

// function name for object attribute synchronization
static const char* funcobjsync = "objectsync";

// function name for proxy creation
static const char* funcproxycreate = "createproxy";

// name of Python object's attribute for keeping reference to a corresponding JavaScript object
const char* smobjattrname = "_smjs_";

// name of JS object's property for keeping reference to a corresponding Python object
const char* smobjpropname = "_smjspy_";

static PyObject* smerrorclass = NULL;

static JSClass smjsClassRef = { "ObjectPythonRef", JSCLASS_HAS_RESERVED_SLOTS(1), nullptr };

static PyObject* smjs_open_context(PyObject* module, PyObject* args)
{
   // The SpiderMonkey engine has not yet initialized
 if(!smjsinit)
    {
    SMContext::init();
    smjsinit = true;

    smerrorclass = PyErr_NewException("smjs.jserror", NULL, NULL);
    Py_XINCREF(smerrorclass);
    }

 PyObject* context = NULL;
 if(!PyArg_ParseTuple(args, "O", &context))
    return NULL;

 SMContext* sm = SMContext::open();
 if(sm == NULL) return NULL;
 SMPythonContext* pytcx = new SMPythonContext(sm);

 PyObject* capsule = PyCapsule_New(pytcx, NULL, NULL);
 if(capsule == NULL)
    { sm->close(); delete sm; delete pytcx; return NULL; }

 if(PyObject_SetAttrString(context, smattrname, capsule) != 0)
    { sm->close(); delete sm; delete pytcx; return NULL; }

 Py_RETURN_NONE;
}

static SMPythonContext* getcontext(PyObject* context)
{
 PyObject* capsule = PyObject_GetAttrString(context, smattrname);
 if(capsule == NULL) return NULL;

 return (SMPythonContext*)PyCapsule_GetPointer(capsule, NULL);
}

static PyObject* smjs_init_context(PyObject* module, PyObject* args)
{
 PyObject* context = NULL;
 if(!PyArg_ParseTuple(args, "O", &context))
    return NULL;

 SMPythonContext* pytcx = getcontext(context);
 if(pytcx == NULL) return NULL;

 PyObject* pyglobal = PyObject_GetAttrString(context, globalattrname);
 smjs_bindobjects(context, pytcx->sm->root, pyglobal);
 Py_XDECREF(pyglobal);

 Py_RETURN_NONE;
}

static PyObject* smjs_close_context(PyObject* module, PyObject* args)
{
 PyObject* context = NULL;
 if(!PyArg_ParseTuple(args, "O", &context))
    return NULL;

 SMPythonContext* pytcx = getcontext(context);
 if(pytcx == NULL) return NULL;

 pytcx->sm->close(); delete pytcx->sm; delete pytcx;
 PyObject_SetAttrString(context, smattrname, NULL);

 Py_RETURN_NONE;
}

static PyObject* smjs_execute(PyObject* module, PyObject* args)
{
 PyObject* context = NULL;
 char* script = NULL;
 if(!PyArg_ParseTuple(args, "Os", &context, &script))
    return NULL;

 SMPythonContext* pytcx = getcontext(context);
 if(pytcx == NULL) return NULL;

 if(!pytcx->sm->evaluate(script))
    {
    PyErr_SetString(smerrorclass, pytcx->sm->geterror().c_str());
    return NULL;
    }

 Py_RETURN_NONE;
}

static PyObject* smjs_callfunc(PyObject* module, PyObject* args)
{
 PyObject* context = NULL;
 PyObject* capsule = NULL;
 if(!PyArg_ParseTuple(args, "OO", &context, &capsule))
    return NULL;

 SMPythonContext* pytcx = getcontext(context);
 if(pytcx == NULL) return NULL;
 JSContext* ctx = pytcx->sm->context;

 JS::PersistentRootedObject* jpers = (JS::PersistentRootedObject*)PyCapsule_GetPointer(capsule, NULL);
 JS::RootedObject jsobj(ctx, *jpers);
 JS::RootedValue func(ctx, JS::ObjectValue(*jsobj));

// JS::RootedValue func(ctx, *jpers);

// JS::RootedObject* jsobj = (JS::RootedObject*)PyCapsule_GetPointer(capsule, NULL);
// JS::RootedValue func(ctx, JS::ObjectValue(* (*jsobj) ) );

 JS::RootedValue rval(ctx);
 if(! JS_CallFunctionValue(ctx, nullptr, func, JS::HandleValueArray::empty(), &rval))
    return NULL;

 JS::MutableHandleValue rv(&rval);
 return smjs_convertsingle(ctx, context, rv);
}

void smjs_bindobjects(PyObject* context, JS::RootedObject* jsobj, PyObject* pyobject)
{
 // setting cross-reference from JS to Python
 JS::SetReservedSlot(*jsobj, SlotPtr, JS::PrivateValue(pyobject));

 // setting cross-reference from Python to JS
 PyObject* capsule = PyCapsule_New(jsobj, NULL, NULL);
 PyObject_SetAttrString(pyobject, smobjattrname, capsule);

 // synchronize JS object with python attributes
 PyObject* function = PyObject_GetAttrString(context, funcobjsync);
 PyObject* result = PyObject_CallFunctionObjArgs(function, pyobject, NULL);
 Py_XDECREF(result);
 Py_XDECREF(function);
}

PyObject* smjs_bindnativeobjects(JSContext* ctx, PyObject* context, JS::RootedObject* jsobj)
{
 JS::PersistentRootedObject* jpers = new JS::PersistentRootedObject(ctx, *jsobj);
   // creating reference to a JS object
 PyObject* capsule = PyCapsule_New(jpers, NULL, NULL);

   // creating python proxy object, XDECREF is safe because all proxies are stored in array in context
 PyObject* function = PyObject_GetAttrString(context, funcproxycreate);
 PyObject* pyobject = PyObject_CallFunctionObjArgs(function, capsule, NULL);
 Py_XDECREF(pyobject);
 Py_XDECREF(function);

 // setting cross-reference from JS to Python
 JS::RootedObject jsrefobj(ctx, JS_NewObject(ctx, &smjsClassRef));
 JS::RootedValue vprop(ctx, JS::ObjectValue(*jsrefobj) );
 JS::SetReservedSlot(jsrefobj, SlotPtr, JS::PrivateValue(pyobject));
 JS_SetProperty(ctx, *jsobj, smobjpropname, vprop );
 return pyobject;
}

/* This is a function for calling python global functions that are mapped via smjs_add_globalfunction
 * It is called by SpiderMonkey proxy function with python name and JS args provided
 *
 * There are following steps:
 *  1) obtain python function entry point (funccall attribute of capsuled object)
 *  2) convert name and JS args into Python object
 *  3) call the python entry point
 *  4) cleanup
 */
static bool proxycall(std::string& name, void* proxydata, JSContext* ctx, JS::CallArgs& args)
{
 PyObject* context = (PyObject*)proxydata;

 jsconv_t* convertors = smjs_getconvertors(ctx, args);
 if(convertors == NULL)
     return false;

 // object (self)
 PyObject* pyobject = getpyobjfromjs(ctx, args);
 if(pyobject == NULL) return false;

 // both are new references
 PyObject* function = PyObject_GetAttrString(context, "funccall");
 PyObject* pname =  PyUnicode_FromString(name.c_str());

 PyObject* pargs = smjs_convert(ctx, context, args, convertors);
 if(pargs != NULL)
   {
   PyObject* result = PyObject_CallFunctionObjArgs(function, pyobject, pname, pargs, NULL);
   if(result == NULL)
       {
       Py_XDECREF(pargs); Py_XDECREF(pname); Py_XDECREF(function);
       delete[] convertors;
       std::string error = std::format("Failed to call function {}", name);
       JS_ReportErrorUTF8(ctx, error.c_str());
       return NULL;
       }
   smjs_convertresult(ctx, context, args, result);
   Py_XDECREF(result);
   }

 Py_XDECREF(pargs);
 Py_XDECREF(pname); Py_XDECREF(function);
 delete[] convertors;
 return true;
}

PyObject* getpyobjfromjs(JSContext* ctx, JS::CallArgs& args)
{
 JS::RootedObject thisObj(ctx);
 if(!args.computeThis(ctx, &thisObj)) return NULL;

 return JS::GetMaybePtrFromReservedSlot<PyObject>(thisObj, SlotPtr);
}

// callback from JS engine for getting an attribute
bool proxygetter(std::string& name, void* proxydata, JSContext* ctx, JS::CallArgs& args)
{
 PyObject* context = (PyObject*)proxydata;

 PyObject* pyobject = getpyobjfromjs(ctx, args);
 if(pyobject == NULL) return false;

 PyObject* result = PyObject_GetAttrString(pyobject, name.c_str());
 bool ret = smjs_convertresult(ctx, context, args, result);
 Py_XDECREF(result);

 return ret;
}

// callback from JS engine for setting an attribute
bool proxysetter(std::string& name, void* proxydata, JSContext* ctx, JS::CallArgs& args)
{
 if(args.length() < 1) return false;

 PyObject* pyobject = getpyobjfromjs(ctx, args);
 if(pyobject == NULL) return false;

 PyObject* value = smjs_convertsingle(ctx, (PyObject*)proxydata, args[0]);
 if(value == NULL) return false;

 PyObject_SetAttrString(pyobject, name.c_str(), value);
 return true;
}

static PyObject* smjs_add_objectproperty(PyObject* module, PyObject* args)
{
 PyObject* context = NULL;
 char* name = NULL;
 PyObject* pyobject = NULL;
 if(!PyArg_ParseTuple(args, "OOs", &context, &pyobject, &name))
    return NULL;

 SMPythonContext* pytcx = getcontext(context);
 if(pytcx == NULL) return NULL;

// retrieving reference to the corresponding JS object
 PyObject* capsule = PyObject_GetAttrString(pyobject, smobjattrname);
 JS::RootedObject* jsobj = (JS::RootedObject*)PyCapsule_GetPointer(capsule, NULL);
 if(capsule == NULL) return NULL;

 pytcx->sm->addproxyproperty(name, jsobj, proxygetter, proxysetter, context);

 Py_RETURN_NONE;
}

static PyObject* smjs_add_objectfunction(PyObject* module, PyObject* args)
{
 PyObject* context = NULL;
 char* name = NULL;
 PyObject* pyobject = NULL;
 if(!PyArg_ParseTuple(args, "OOs", &context, &pyobject, &name))
    return NULL;

 SMPythonContext* pytcx = getcontext(context);
 if(pytcx == NULL) return NULL;

// retrieving reference to the corresponding JS object
 PyObject* capsule = PyObject_GetAttrString(pyobject, smobjattrname);
 if(capsule == NULL) return NULL;
 JS::RootedObject* jsobj = (JS::RootedObject*)PyCapsule_GetPointer(capsule, NULL);

 pytcx->sm->addproxyfunction(name, jsobj, proxycall, context);

 Py_RETURN_NONE;
}


static PyObject* smjs_shutdown(PyObject* module, PyObject* args)
{
 Py_XDECREF(smerrorclass);
 Py_CLEAR(smerrorclass);

 if(smjsinit)
     SMContext::shutdown();
 Py_RETURN_NONE;
}

static PyMethodDef smjs_methods[] =
{
 {"open_context", smjs_open_context, METH_VARARGS, "Opens a SpiderMonkey JavaScript context"},
 {"init_context", smjs_init_context, METH_VARARGS, "Initializes a SpiderMonkey JavaScript context"},
 {"close_context", smjs_close_context, METH_VARARGS, "Closes a SpiderMonkey JavaScript context"},
 {"execute", smjs_execute, METH_VARARGS, "Execute a JavaScript"},
 {"callfunc", smjs_callfunc, METH_VARARGS, "Calls a JavaScript function"},
// {"add_globalfunction", smjs_add_globalfunction, METH_VARARGS, "Adds a global function to the JavaScript"},
// {"add_globalobject", smjs_add_globalobject, METH_VARARGS, "Adds a global object to the JavaScript"},
 {"add_objectproperty", smjs_add_objectproperty, METH_VARARGS, "Adds a property to an object"},
 {"add_objectfunction", smjs_add_objectfunction, METH_VARARGS, "Adds a function to an object"},
 {"shutdown", smjs_shutdown, METH_VARARGS, "Shutdowns the SpiderMoney JavaScript engine"},
 {NULL, NULL, 0, NULL}
};

static struct PyModuleDef smjs_module =
{
 PyModuleDef_HEAD_INIT,
 "smjs",
 "Python interface to Mozilla SpiderMonkey library",
 -1,
 smjs_methods
};

PyMODINIT_FUNC PyInit_smjs(void)
{
 return PyModule_Create(&smjs_module);
}