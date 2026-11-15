using System;using System.IO;using System.Text;using System.Runtime.InteropServices;using System.Collections.Generic;using SolidWorks.Interop.sldworks;
public class AsmExport {
static ISldWorks a;
public static void Run(string asm,string outDir){
 try{
  try{a=(ISldWorks)Marshal.GetActiveObject("SldWorks.Application");}
  catch{Type t=Type.GetTypeFromProgID("SldWorks.Application");a=(ISldWorks)Activator.CreateInstance(t);}
  a.Visible=false;
  if(!Directory.Exists(outDir))Directory.CreateDirectory(outDir);
  foreach(string f in Directory.GetFiles(outDir,"*.STL")){try{File.Delete(f);}catch{}}
  int e=0,w=0;
  IModelDoc2 d=(IModelDoc2)a.OpenDoc6(asm,2,1,"",ref e,ref w);
  if(d==null){Console.WriteLine("OPEN FAIL e="+e);return;}
  Console.WriteLine("opened "+d.GetTitle());
  int e2=0,w2=0;
  string target=Path.Combine(outDir,"ASM.STL");
  bool ok=d.Extension.SaveAs(target,0,2,null,ref e2,ref w2);
  Console.WriteLine("saveas ok="+ok+" err="+e2);
  string[] got=Directory.GetFiles(outDir,"*");
  Console.WriteLine("files="+got.Length);
  foreach(string f in got)Console.WriteLine("  "+Path.GetFileName(f)+"  "+new FileInfo(f).Length);
  a.CloseDoc(d.GetTitle());
 }catch(Exception ex){Console.WriteLine("EX "+ex.GetType().Name+": "+ex.Message);}
 finally{if(a!=null){try{a.ExitApp();}catch{}}}
}
}
