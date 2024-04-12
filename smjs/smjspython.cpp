#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <iostream>
#include "smjspython.h"
#include <js/CompilationAndEvaluation.h>
#include <js/Conversions.h>
#include <js/Object.h>

static bool smjsinit = false;
static const char* smattrname = "sm";

// name of Python object's attribute for keeping reference to a corresponding JavaScript object
static const char* smobjattrname = "_smjs_";

static PyObject* smerrorclass = NULL;
static JSClass smjsClass = { "Object", JSCLASS_HAS_RESERVED_SLOTS(1), nullptr };
enum smjsClassSlots { SlotPtr };

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

 // both are new references
 PyObject* function = PyObject_GetAttrString(context, "funccall");
 PyObject* pname =  PyUnicode_FromString(name.c_str());

 PyObject* pargs = smjs_convert(ctx, args, convertors);
 if(pargs != NULL)
   {
   PyObject* result = PyObject_CallFunctionObjArgs(function, pname, pargs, NULL);
   smjs_convertresult(ctx, args, result);
   Py_XDECREF(result);
   }

 Py_XDECREF(pargs);
 Py_XDECREF(pname); Py_XDECREF(function);
 delete[] convertors;
 return true;
}

static PyObject* smjs_add_globalfunction(PyObject* module, PyObject* args)
{
 PyObject* context = NULL;
 char* name = NULL;
 if(!PyArg_ParseTuple(args, "Os", &context, &name))
    return NULL;

 SMPythonContext* pytcx = getcontext(context);
 if(pytcx == NULL) return NULL;

 pytcx->sm->addproxyfunction(name, proxycall, context);

 Py_RETURN_NONE;
}

// This function creates a mirrored JavaScript object and connects both (Python and JavaScript object)
// with cross-references. This function does not create any attribute
static PyObject* smjs_add_globalobject(PyObject* module, PyObject* args)
{
 PyObject* context = NULL;
 char* name = NULL;
 PyObject* pyobject = NULL;
 if(!PyArg_ParseTuple(args, "OsO", &context, &name, &pyobject))
    return NULL;

 SMPythonContext* pytcx = getcontext(context);
 if(pytcx == NULL) return NULL;

// new JS object
 JS::RootedObject* jsobj = new JS::RootedObject(pytcx->sm->context, JS_NewObject(pytcx->sm->context, &smjsClass));
 if(!(*jsobj)) return NULL;

// setting cross-reference from JS to Python
 JS::SetReservedSlot(*jsobj, SlotPtr, JS::PrivateValue(pyobject));

// setting cross-reference from Python to JS
 PyObject* capsule = PyCapsule_New(jsobj, NULL, NULL);
 PyObject_SetAttrString(pyobject, smobjattrname, capsule);

// Adding new JS object to the global JS object
 JS::RootedValue value(pytcx->sm->context); value.setObject(*(*jsobj));
 if(!JS_SetProperty(pytcx->sm->context, *(pytcx->sm->root), name, value))
    return NULL;

 Py_RETURN_NONE;
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
 PyObject* pyobject = getpyobjfromjs(ctx, args);
 if(pyobject == NULL) return false;

 PyObject* result = PyObject_GetAttrString(pyobject, name.c_str());
 smjs_convertresult(ctx, args, result);
 Py_XDECREF(result);

 return true;
}

// callback from JS engine for setting an attribute
bool proxysetter(std::string& name, void* proxydata, JSContext* ctx, JS::CallArgs& args)
{
 if(args.length() < 1) return false;

 PyObject* pyobject = getpyobjfromjs(ctx, args);
 if(pyobject == NULL) return false;

 PyObject* value = smjs_convertsingle(ctx, args[0]);
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
 {"add_globalfunction", smjs_add_globalfunction, METH_VARARGS, "Adds a global function to the JavaScript"},
 {"add_globalobject", smjs_add_globalobject, METH_VARARGS, "Adds a global object to the JavaScript"},
 {"add_objectproperty", smjs_add_objectproperty, METH_VARARGS, "Adds a property to an object"},
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