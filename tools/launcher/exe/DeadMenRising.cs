// "KL Dead Men Rising.exe" - the tester-facing launcher start (owner, 2026-11-09: "maybe an .exe ... since theres a .cmd in
// the background it looks off? i want it to look production quality"). Replaces KLMerge.bat, which left a minimized
// console in the taskbar the whole time.
//
// What it does: runs KLMergeLauncher.ps1 (beside the exe) IN THIS PROCESS through the PowerShell engine Windows ships
// (System.Management.Automation, GAC), on this STA thread (WPF needs STA), execution policy Bypass for this runspace
// only (the machine's policy is not touched). No powershell.exe is started, so no console window exists at all, and
// the taskbar shows this exe's icon. The .ps1 stays plain text beside the exe: what runs is still readable.
// One launcher at a time: a second start brings the open window to the front and exits.
//
// Build: build.bat (the .NET Framework 4 csc.exe that every Windows 10/11 has; no SDK). Unsigned: SmartScreen shows
// "Windows protected your PC" on the first start from a download (More info > Run anyway) until it is code-signed.
using System;
using System.IO;
using System.Management.Automation;
using System.Management.Automation.Runspaces;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyTitle("KL: Dead Men Rising")]
[assembly: AssemblyDescription("KL: Dead Men Rising launcher")]
[assembly: AssemblyProduct("KL: Dead Men Rising")]
[assembly: AssemblyCompany("KL: Dead Men Rising (fan project, in contribution with luvsic)")]
[assembly: AssemblyCopyright("Fan-made mod. Kane & Lynch is a trademark of its owners.")]
[assembly: AssemblyVersion("1.0.0.0")]
[assembly: AssemblyFileVersion("1.0.0.0")]
[assembly: AssemblyInformationalVersion("1.0.0")]

static class DeadMenRising
{
    const string Title = "KL: Dead Men Rising";
    const string Script = "KLMergeLauncher.ps1";

    [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern IntPtr FindWindow(string cls, string title);

    [STAThread]
    static int Main(string[] args)
    {
        string here = AppDomain.CurrentDomain.BaseDirectory;
        string ps1 = Path.Combine(here, Script);
        string log = Path.Combine(here, "KLMergeLauncher.log");

        bool first;
        using (var one = new Mutex(true, "Local\\KLDeadMenRisingLauncher", out first))
        {
            if (!first)
            {
                // the window title is set in the .ps1's XAML; hidden while the game runs (then there is nothing to show)
                IntPtr w = FindWindow(null, Title);
                if (w != IntPtr.Zero) { if (IsIconic(w)) ShowWindow(w, 9); SetForegroundWindow(w); }
                return 0;
            }
            if (!File.Exists(ps1))
            {
                Fail(log, Script + " is not beside " + Path.GetFileName(Application.ExecutablePath) +
                     ". Run \"KL Dead Men Rising Setup.bat\" again (it puts the launcher files in this folder).");
                return 2;
            }
            try
            {
                var iss = InitialSessionState.CreateDefault();
                iss.ExecutionPolicy = Microsoft.PowerShell.ExecutionPolicy.Bypass;
                iss.ApartmentState = ApartmentState.STA;
                iss.ThreadOptions = PSThreadOptions.UseCurrentThread;
                using (Runspace rs = RunspaceFactory.CreateRunspace(iss))
                {
                    rs.Open();
                    using (PowerShell ps = PowerShell.Create())
                    {
                        ps.Runspace = rs;
                        ps.AddCommand(ps1);                     // as a script file: $MyInvocation / $PSScriptRoot stay right
                        for (int i = 0; i + 1 < args.Length; i += 2)   // -Package <folder> (the only parameter the .ps1 has)
                            if (args[i].TrimStart('-', '/').Equals("Package", StringComparison.OrdinalIgnoreCase))
                                ps.AddParameter("Package", args[i + 1]);
                        ps.Invoke();
                        // the .ps1 shows its own error box (its trap); this catches what never reached the script
                        if (ps.Streams.Error.Count > 0 && !ScriptRan(ps.Streams.Error))
                            Fail(log, ps.Streams.Error[0].ToString());
                    }
                }
            }
            catch (Exception e)
            {
                Fail(log, e.GetType().Name + ": " + e.Message);
                return 1;
            }
        }
        return 0;
    }

    // an error that came out of the running script (its trap already said it) vs. one from loading it
    static bool ScriptRan(System.Collections.Generic.IEnumerable<ErrorRecord> errs)
    {
        foreach (ErrorRecord r in errs)
            if (r.InvocationInfo != null && r.InvocationInfo.ScriptLineNumber > 0) return true;
        return false;
    }

    static void Fail(string log, string msg)
    {
        string line = "[" + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "] launcher exe: " + msg;
        try { File.AppendAllText(log, line + Environment.NewLine, Encoding.UTF8); } catch { }
        MessageBox.Show("The " + Title + " launcher could not start:\r\n\r\n" + msg +
                        "\r\n\r\nPlease send KLMergeLauncher.log (beside the launcher) to @r6c0 on Discord.",
                        Title, MessageBoxButtons.OK, MessageBoxIcon.Error);
    }
}
