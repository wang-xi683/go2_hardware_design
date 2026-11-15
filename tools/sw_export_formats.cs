using System;using System.IO;using System.Text;using System.Runtime.InteropServices;using System.Collections.Generic;using SolidWorks.Interop.sldworks;
public class ExportFormats {
static ISldWorks a;
// 读取 TSV: src \t stepOut \t stlOut  （输出为空表示不导出该格式）
public static void Run(string listPath){
 try{
  try{a=(ISldWorks)Marshal.GetActiveObject("SldWorks.Application");}
  catch{Type t=Type.GetTypeFromProgID("SldWorks.Application");a=(ISldWorks)Activator.CreateInstance(t);}
  a.Visible=false;
  string[] lines=File.ReadAllLines(listPath,new UTF8Encoding(false));
  int okStep=0,okStl=0,fail=0;
  foreach(string raw in lines){
   string line=raw.Trim();
   if(line.Length==0||line.StartsWith("#"))continue;
   string[] c=line.Split('\t');
   if(c.Length<3)continue;
   string src=c[0].Trim(), stepOut=c[1].Trim(), stlOut=c[2].Trim();
   if(!File.Exists(src)){Console.WriteLine("MISSING SRC "+src);fail++;continue;}
   int e=0,w=0;
   IModelDoc2 d=(IModelDoc2)a.OpenDoc6(src,1,1,"",ref e,ref w);   // 1=part
   if(d==null){
     d=(IModelDoc2)a.OpenDoc6(src,2,1,"",ref e,ref w);            // 2=assembly
   }
   if(d==null){Console.WriteLine("OPEN FAIL e="+e+"  "+Path.GetFileName(src));fail++;continue;}
   string baseName=Path.GetFileNameWithoutExtension(src);
   if(stepOut.Length>0){
     string dir=Path.GetDirectoryName(stepOut);
     if(!Directory.Exists(dir))Directory.CreateDirectory(dir);
     try{if(File.Exists(stepOut))File.Delete(stepOut);}catch{}
     int e1=0,w1=0;
     bool ok=d.Extension.SaveAs(stepOut,0,2,null,ref e1,ref w1);
     if(ok&&File.Exists(stepOut)){okStep++;Console.WriteLine("STEP ok  "+Path.GetFileName(stepOut)+"  "+new FileInfo(stepOut).Length);}
     else{
       // SW 可能追加 " - 零件名" 后缀
       string dirx=Path.GetDirectoryName(stepOut);
       string stem=Path.GetFileNameWithoutExtension(stepOut);
       bool moved=false;
       foreach(string f in Directory.GetFiles(dirx,stem+"*")){
         string fn=Path.GetFileNameWithoutExtension(f);
         if(fn.Equals(stem,StringComparison.OrdinalIgnoreCase))continue;
         if(fn.StartsWith(stem)){
           try{if(File.Exists(stepOut))File.Delete(stepOut);File.Move(f,stepOut);moved=true;okStep++;
             Console.WriteLine("STEP ok* "+Path.GetFileName(stepOut)+"  "+new FileInfo(stepOut).Length);}catch{}
           break;
         }
       }
       if(!moved){Console.WriteLine("STEP FAIL err="+e1+"  "+Path.GetFileName(src));fail++;}
     }
   }
   if(stlOut.Length>0){
     string dir=Path.GetDirectoryName(stlOut);
     if(!Directory.Exists(dir))Directory.CreateDirectory(dir);
     try{if(File.Exists(stlOut))File.Delete(stlOut);}catch{}
     int e2=0,w2=0;
     bool ok=d.Extension.SaveAs(stlOut,0,2,null,ref e2,ref w2);
     string stem=Path.GetFileNameWithoutExtension(stlOut);
     bool done=false;
     if(ok&&File.Exists(stlOut)){done=true;}
     if(!done){
       string dirx=Path.GetDirectoryName(stlOut);
       foreach(string f in Directory.GetFiles(dirx,stem+"*")){
         string fn=Path.GetFileNameWithoutExtension(f);
         if(fn.Equals(stem,StringComparison.OrdinalIgnoreCase)){done=true;break;}
         if(fn.StartsWith(stem)){
           try{if(File.Exists(stlOut))File.Delete(stlOut);File.Move(f,stlOut);done=true;}catch{}
           break;
         }
       }
     }
     if(done){okStl++;Console.WriteLine("STL  ok  "+Path.GetFileName(stlOut)+"  "+new FileInfo(stlOut).Length);}
     else{Console.WriteLine("STL  FAIL err="+e2+"  "+Path.GetFileName(src));fail++;}
   }
   try{a.CloseDoc(d.GetTitle());}catch{}
  }
  Console.WriteLine("=== STEP="+okStep+"  STL="+okStl+"  FAIL="+fail);
 }catch(Exception ex){Console.WriteLine("EX "+ex.GetType().Name+": "+ex.Message);}
 finally{if(a!=null){try{a.ExitApp();}catch{}}}
}
}
