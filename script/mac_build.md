## Build MacOs Kalama Browser

### Install prerequisites

Follow the instructions for your platform:

rust 1.57+  
node 14+  
Xcode 13.1+  
macOS SDK 12.0+  
[Packages](http://s.sudre.free.fr/Software/Packages/about.html)

[note]
Build Kalama Browser code must be use Xcode Developer tool

```bash
xcode-select -s /Applications/Xcode.app/Contents/Developer
```

### Clone and initialize the repo

Once you have the prerequisites installed, you can get the code and initialize the build environment.

1. download depot_tools and set env variables

```bash
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git

export PATH="$PATH:${path_to_depot_tools}"
```

##### disable update chromium source background

```bash
export DEPOT_TOOLS_UPDATE=0
```

2.Get Kalama Browser and Chromium source

```bash
export root=browser
git clone https://github.com/kalama-io/browser ${root}

cd ${root}

fetch chromium

gclient sync --force --nohooks --with_branch_heads

cd ${root}/src

git fetch --tags

git checkout -b kalama_branch 117.0.5938.153

gclient sync --with_branch_heads --with_tags
```

### Build Kalama Browser

1. Compile Kalama Browser source code
   [note] if you build machine is macos, you must to set target-cpu argument like `ARM` and `X86`
   ARM is mean m1 cpu machine, and X86 is mean x86 cpu machine

```bash
cd ${root}/script

python(python3) build.py --project-name=${project_name} --version=${version} --target-cpu=${target_cpu} --channel=${channel}

### like this: python(python3) build.py --project-name=Browser --version=1 --target-cpu=ARM --channel=beta
```

2.Find the Kalama Browser installation package

`${root}/dmg/${target_cpu}/kalama-browser-installer-${version}.dmg`
