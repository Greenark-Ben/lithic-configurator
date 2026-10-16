using System;
using System.IO;
using System.IO.Compression;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.ApplicationServices;
using DesignAutomationFramework;
using IronPython.Hosting;

namespace Lithic.WindowFixed.Cloud
{
    public sealed class CloudApplication : IExternalDBApplication
    {
        public ExternalDBApplicationResult OnStartup(ControlledApplication app)
        {
            DesignAutomationBridge.DesignAutomationReadyEvent += Run;
            return ExternalDBApplicationResult.Succeeded;
        }
        public ExternalDBApplicationResult OnShutdown(ControlledApplication app)
        {
            DesignAutomationBridge.DesignAutomationReadyEvent -= Run;
            return ExternalDBApplicationResult.Succeeded;
        }
        private static void Run(object sender, DesignAutomationReadyEventArgs args)
        {
            args.Succeeded = false;
            string root = Directory.GetCurrentDirectory();
            string output = Path.Combine(root, "results");
            Directory.CreateDirectory(output);
            try
            {
                if (args.DesignAutomationData.RevitApp.VersionNumber != "2024")
                    throw new InvalidOperationException("This proof requires Revit 2024.");
                string content = Path.GetDirectoryName(typeof(CloudApplication).Assembly.Location);
                var engine = Python.CreateEngine();
                engine.Runtime.LoadAssembly(typeof(Document).Assembly);
                var paths = new List<string>(engine.GetSearchPaths());
                paths.Add(content);
                paths.Add(Path.Combine(content, "Lib"));
                engine.SetSearchPaths(paths);
                engine.Runtime.IO.SetOutput(Console.OpenStandardOutput(), System.Text.Encoding.UTF8);
                engine.Runtime.IO.SetErrorOutput(Console.OpenStandardError(), System.Text.Encoding.UTF8);
                var scope = engine.CreateScope();
                scope.SetVariable("application", args.DesignAutomationData.RevitApp);
                scope.SetVariable("input_root", Path.Combine(root, "input"));
                scope.SetVariable("output_root", output);
                engine.ExecuteFile(Path.Combine(content, "cloud_entry.py"), scope);
                args.Succeeded = scope.GetVariable<bool>("cloud_geometry_passed");
                engine.Runtime.Shutdown();
            }
            catch (Exception error)
            {
                Console.Error.WriteLine(error);
                File.WriteAllText(Path.Combine(output, "cloud-error.txt"), error.ToString());
            }
            finally
            {
                string archive = Path.Combine(root, "results.zip");
                if (File.Exists(archive)) File.Delete(archive);
                ZipFile.CreateFromDirectory(output, archive);
            }
        }
    }
}
