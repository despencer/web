#include <iostream>
#include "smjs.h"
#include <js/SourceText.h>
#include <js/CompilationAndEvaluation.h>
#include <js/Conversions.h>
#include <js/Object.h>

typedef void* pvoid_t;

SMFunction::SMFunction(jsfunc_t f, unsigned int n, jstype_t* a)
{
 function = f;
 numargs = n;
 argtypes = a;
}

bool SMFunction::call(JSContext* ctx, JS::CallArgs& args)
{
 pvoid_t* cargs = new pvoid_t[this->numargs+1];

 JS::RootedString message(ctx, args[0].toString());
 std::string ptr = JS_EncodeStringToUTF8(ctx, message).get();
 cargs[1] = &ptr;
 bool ret = this->function(cargs);
 delete[] cargs;
 return ret;
}

bool SMContext::init(void)
{
 if(!JS_Init())
     {
     std::cerr << "Can't initialize Spider Monkey\n";
     return false;
     }
 return true;
}

void SMContext::shutdown(void)
{
 JS_ShutDown();
}

static JSClass SMGlobalClass = { "global", JSCLASS_GLOBAL_FLAGS, &JS::DefaultGlobalClassOps };

SMContext* SMContext::open(void)
{
 JSContext* jscontext = JS_NewContext(JS::DefaultHeapMaxBytes);
 if(jscontext == NULL)
    {
    std::cerr << "Can't create JSContext\n";
    return NULL;
    }
 SMContext* context = new SMContext();
 context->context = jscontext;
 JS_SetContextPrivate(jscontext, context);

 JS::InitSelfHostedCode(context->context);

 context->options = new JS::RealmOptions();
 context->global = JS_NewGlobalObject(context->context, &SMGlobalClass, nullptr, JS::FireOnNewGlobalHook, *context->options);
 context->root = new JS::RootedObject(context->context, context->global);
 context->realm = new JSAutoRealm(context->context, *context->root);
 return context;
}

void SMContext::close(void)
{
 delete realm;
 delete root;
 delete options;
 JS_DestroyContext(context);
 context = NULL;

 for(auto & ft : functions)
      delete ft.second;
 functions.clear();
 for(auto & fpt : proxyfuncs)
      delete fpt.second;
 proxyfuncs.clear();
}

bool SMContext::evaluate(const char* script)
{
 JS::CompileOptions* options = new JS::CompileOptions(this->context);
 options->setFileAndLine("script", 1);

 JS::SourceText<mozilla::Utf8Unit>* source = new JS::SourceText<mozilla::Utf8Unit>();
 bool ret = source->init(this->context, script, strlen(script), JS::SourceOwnership::Borrowed);

 JS::RootedValue* result =  new JS::RootedValue(this->context);

 if(ret)
    ret = JS::Evaluate(this->context, *options, *source, result);

 delete result;
 delete source;
 delete options;

 return ret;
}

std::string SMContext::geterror(void)
{
 if(!JS_IsExceptionPending(this->context))
    return std::string("No error");

 JS::RootedValue* excpt = new JS::RootedValue(this->context);
 JS_GetPendingException(this->context, excpt);
 JS_ClearPendingException(this->context);

 std::string ret;

 {
  JS::RootedString message(this->context, JS::ToString(this->context, *excpt));
  if(!message)
      ret = "Unable to convert the exception to a string";
  else
      ret = JS_EncodeStringToUTF8(this->context, message).get();
 }

 delete excpt;
 return ret;
}

void SMContext::reporterror(std::ostream& str)
{
 str << geterror();
}

bool cppnative(JSContext* ctx, unsigned argc, JS::Value* vp)
{
 SMContext* context = (SMContext*)JS_GetContextPrivate(ctx);
 JS::CallArgs args = JS::CallArgsFromVp(argc, vp);
 JSFunction* func = (JSFunction*)&args.callee();
 if(auto search = context->functions.find(func); search != context->functions.end())
     return search->second->call(ctx, args);
 std::cerr << "Unable to find function pointer\n";
 return false;
}

bool proxyfunc(JSContext* ctx, unsigned argc, JS::Value* vp)
{
 SMContext* context = (SMContext*)JS_GetContextPrivate(ctx);
 JS::CallArgs args = JS::CallArgsFromVp(argc, vp);
 JSFunction* func = (JSFunction*)&args.callee();
 if(auto search = context->proxyfuncs.find(func); search != context->proxyfuncs.end())
     return search->second->call(ctx, args);
 std::cerr << "Unable to find function pointer\n";
 return false;
}

bool SMContext::addfunction(const char* name, jsfunc_t func, unsigned int numargs, jstype_t* argtypes)
{
 JSFunction* jsfunc = JS_DefineFunction(this->context, *this->root, name, cppnative, 0, 0);
 SMFunction* smf = new SMFunction(func, numargs, argtypes);
 functions.insert(std::make_pair(jsfunc, smf));
 return true;
}

bool SMContext::addproxyfunction(const char* name, jsfuncproxy_t func, void* proxydata)
{
 JSFunction* jsfunc = JS_DefineFunction(this->context, *this->root, name, proxyfunc, 0, 0);
 SMProxyFunction* pmf = new SMProxyFunction(name, func, proxydata);
 proxyfuncs.insert(std::make_pair(jsfunc, pmf));
 return true;
}

bool SMContext::addproxyproperty(const char* name, JS::RootedObject* jsobj, jsfuncproxy_t getter, jsfuncproxy_t setter, void* proxydata)
{
 // making getter and setter JS function with the reference to the native C++ functions
 // then register it as an JS object getter and setter attribute
 JSFunction* jsgetter = JS_DefineFunction(context, *root, name, proxyfunc, 0, 0);
 JS::RootedObject vgetter(context, JS_GetFunctionObject(jsgetter));
 JSFunction* jssetter = JS_DefineFunction(context, *root, name, proxyfunc, 0, 0);
 JS::RootedObject vsetter(context, JS_GetFunctionObject(jssetter));

 JS_DefineProperty(context, *(jsobj), name, vgetter, vsetter, JSPROP_ENUMERATE);

 proxyfuncs.insert(std::make_pair(jsgetter, new SMProxyFunction(name, getter, proxydata)));
 proxyfuncs.insert(std::make_pair(jssetter, new SMProxyFunction(name, setter, proxydata)));
 return true;
}