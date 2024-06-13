#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <iostream>
#include <format>
#include <js/Object.h>
#include "smjspython.h"

extern const char* smobjattrname;
static JSClass smjsClass = { "Object", JSCLASS_HAS_RESERVED_SLOTS(1), nullptr };
extern JSClass SMGlobalClass;

PyObject* smjs_conv_string(JSContext* ctx, const JS::MutableHandleValue& value)
{
 JS::RootedString strvalue(ctx, value.toString());
 std::string str = JS_EncodeStringToUTF8(ctx, strvalue).get();
 return PyUnicode_FromString(str.c_str());
}

PyObject* smjs_conv_int32(JSContext* ctx, const JS::MutableHandleValue& value)
{
 long pval = value.toInt32();
 return PyLong_FromLong(pval);
}

PyObject* smjs_conv_object(JSContext* ctx, const JS::MutableHandleValue& value)
{
 JSObject* jobj = &value.toObject();
 return JS::GetMaybePtrFromReservedSlot<PyObject>(jobj, SlotPtr);
}

PyObject* smjs_conv_none(JSContext* ctx, const JS::MutableHandleValue& value)
{
 Py_RETURN_NONE;
}

jsconv_t smjs_getconvertor(JSContext* ctx, const JS::MutableHandleValue& value)
{
 if(value.isString())
     return smjs_conv_string;
 else if(value.isUndefined() || value.isNull())
     return smjs_conv_none;
 else if(value.isObject())
    {
    const JSClass* jcls = JS::GetClass(&value.toObject());
    if (jcls == &smjsClass || jcls == &SMGlobalClass)
        return smjs_conv_object;
    JS_ReportErrorUTF8(ctx, "Native objects are not yet implemented");
    return NULL;
    }
 else if(value.isInt32())
    return smjs_conv_int32;
 else
    {
    uint64_t data = *(uint64_t*)(void*)&value;
    data = data >> 47;
    std::string error = std::format("Unrecongnized JS type {:X}", data);
    JS_ReportErrorUTF8(ctx, error.c_str());
    return NULL;
    }
 return NULL;
}

jsconv_t* smjs_getconvertors(JSContext* ctx, JS::CallArgs& args)
{
 unsigned int len = 1;
 if(args.length() > 0) len = args.length();

 jsconv_t* ret = new jsconv_t[len];

 for(unsigned int i=0; i<args.length(); i++)
   {
   ret[i] = smjs_getconvertor(ctx, args[i]);
   if(ret[i] == NULL)
      { delete[] ret; return NULL; }
   }
 return ret;
}

PyObject* smjs_convert(JSContext* ctx, JS::CallArgs& args, jsconv_t* converters)
{
 PyObject* list = PyList_New(0);
 for(unsigned int i=0; i<args.length(); i++)
   PyList_Append(list, converters[i](ctx, args[i]));
 return list;
}

PyObject* smjs_convertsingle(JSContext* ctx, const JS::MutableHandleValue& value)
{
 jsconv_t conv = smjs_getconvertor(ctx, value);
 if(conv == NULL) return NULL;
 return conv(ctx, value);
}

bool smjs_convertresult(JSContext* ctx, PyObject* context, JS::CallArgs& args, PyObject* pobj)
{
 const char* tname = Py_TYPE(pobj)->tp_name;

 if(strcmp(tname, "NoneType") == 0)
    args.rval().setNull();
 else if(strcmp(tname, "str") == 0)
    {
    Py_ssize_t size = 0;
    const char* pstr = PyUnicode_AsUTF8AndSize(pobj, &size);
    JS::ConstUTF8CharsZ buf(pstr, size);
    JS::RootedString str(ctx, JS_NewStringCopyUTF8Z(ctx, buf));
    args.rval().setString(str);
    }
 else if(std::isupper(tname[0]))
    {
    PyObject* capsule = PyObject_GetAttrString(pobj, smobjattrname);
    if(capsule == NULL)
        {
           // create and bind JS Object
        JS::RootedObject* jsobj = new JS::RootedObject(ctx, JS_NewObject(ctx, &smjsClass));
        if(!(*jsobj)) return NULL;
        smjs_bindobjects(context, jsobj, pobj);
        args.rval().setObject(*(*jsobj));
        }
    else
        {
           // JS object already exists
        JS::RootedObject* jsobj = (JS::RootedObject*)PyCapsule_GetPointer(capsule, NULL);
        if(jsobj == NULL)
            {
            std::string error = std::format("Can't resolve JS object for Python object of type {}", tname);
            JS_ReportErrorUTF8(ctx, error.c_str());
            return false;
            }
        args.rval().setObject(*(*jsobj));
        }
    }
 else if(strcmp(tname, "int") == 0)
    {
    long value = PyLong_AsLong(pobj);
    args.rval().setNumber(value);
    }
 else
    {
    std::string error = std::format("Unrecongnized python type {}", tname);
    JS_ReportErrorUTF8(ctx, error.c_str());
    return false;
    }
 return true;
}