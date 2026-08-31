// One-off installer/builder for cPanel's Node.js "Run JS script" box,
// which only runs a .js file path (not shell commands like `npm install`).
// Delete after the frontend has been built once.
const { execSync } = require("child_process");

function run(cmd) {
  console.log(`\n$ ${cmd}`);
  try {
    const output = execSync(cmd, { cwd: __dirname, encoding: "utf-8" });
    console.log(output);
  } catch (err) {
    console.log("STDOUT:", err.stdout);
    console.log("STDERR:", err.stderr);
    throw err;
  }
}

try {
  run("npm install");
  run("npm run build");
  console.log("\nBuild complete.");
} catch (err) {
  console.error("Build failed:", err.message);
  process.exit(1);
}
