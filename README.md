
![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)
# Ladder TinyTapeout

🚀 **Ladder TinyTapeout** is an open-source digital design project built for the [TinyTapeout](https://tinytapeout.com) program.
This project demonstrates how to implement, test, and verify a **Verilog-based ladder logic circuit** that can be synthesized for **FPGA** and fabricated as an **ASIC (Application-Specific Integrated Circuit)** through the TinyTapeout flow.

---

## 📌 Project Overview

This repository contains:

* A **Verilog design** (`project.v`) that implements the ladder-based digital circuit.
* **Testbenches** written in Verilog and Python to verify correctness.
* **GitHub Actions workflows** for automated testing, FPGA synthesis, and GDS generation.
* **Documentation** to support easy usage and replication.

The goal of this project is to showcase the **end-to-end flow of hardware design**:

1. RTL design in Verilog
2. Testbench simulation
3. FPGA prototyping
4. ASIC synthesis (via TinyTapeout)

---

## ✨ Features

* ✅ Ladder logic-inspired Verilog implementation
* ✅ Open-source ASIC-ready design flow
* ✅ Fully tested with Verilog + Python testbenches
* ✅ Supports GTKWave waveform visualization
* ✅ CI/CD workflows for **testing, FPGA, and GDS**
* ✅ Compatible with **TinyTapeout shuttle submission**

---

## 📂 Repository Structure

```
.
├── .devcontainer/          # Dev container for reproducible builds
│   ├── Dockerfile
│   ├── copy_tt_support_tools.sh
│   └── devcontainer.json
│
├── .github/workflows/      # GitHub Actions automation
│   ├── docs.yaml           # Build and deploy docs
│   ├── fpga.yaml           # FPGA synthesis & tests
│   ├── gds.yaml            # ASIC GDS flow
│   └── test.yaml           # Simulation + verification
│
├── .vscode/                # VSCode project configuration
│   ├── extensions.json
│   └── settings.json
│
├── docs/                   # Documentation
│   └── info.md
│
├── src/                    # Source design
│   ├── config.json
│   └── project.v           # Main Verilog design
│
├── test/                   # Testing framework
│   ├── Makefile
│   ├── README.md
│   ├── requirements.txt    # Python dependencies
│   ├── tb.v                # Verilog testbench
│   ├── tb.gtkv             # GTKWave config
│   └── test.py             # Python-based test runner
│
├── .gitignore
├── LICENSE
├── README.md               # Project documentation
└── info.yaml               # TinyTapeout configuration
```

---

## 🔧 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Sruthi192005/ladder_tinytapeout.git
cd ladder_tinytapeout
```

### 2. Install Python Dependencies

```bash
pip install -r test/requirements.txt
```

### 3. Build & Run Simulation

```bash
make -C test
```

### 4. View Waveforms with GTKWave

```bash
gtkwave test/tb.gtkv
```

---

## 🧪 Testing

Two test flows are supported:

### **Verilog Testbench (tb.v)**

Run simulations via `Icarus Verilog` or `Verilator`:

```bash
iverilog -o sim test/tb.v src/project.v
vvp sim
```

### **Python Test (test.py)**

Uses `cocotb` or direct Python drivers for simulation:

```bash
python3 test/test.py
```

---

## 🏷️ GitHub Workflows

The repository uses GitHub Actions for CI/CD automation:

* **`test.yaml`** → Runs simulation tests on every commit
* **`fpga.yaml`** → Builds FPGA bitstreams
* **`gds.yaml`** → Generates GDS layout for ASIC fabrication
* **`docs.yaml`** → Deploys project documentation

You can view workflow runs under the **Actions** tab of this repository.

---

## 💡 FPGA Flow

The design can be deployed on FPGA boards for hardware validation.

* Supported FPGA toolchains (example):

  * Xilinx Vivado
  * Lattice iCE40 (via Yosys + nextpnr)

To run the FPGA workflow locally:

```bash
make fpga
```

---

## 🏠 ASIC (TinyTapeout) Flow

This project is structured to be **TinyTapeout-compatible**.

* `info.yaml` → Defines metadata for submission
* `src/project.v` → RTL design for synthesis
* Workflows (`gds.yaml`) → Generate final ASIC layout

By submitting to TinyTapeout, this design can be fabricated into silicon.

---

## 🤝 Contribution Guide

Contributions are welcome! 🚀

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Submit a Pull Request

Please ensure your contributions include:

* Proper documentation
* Passing test cases

---

## 📜 License

This project is licensed under the **MIT License**.
See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

* [TinyTapeout](https://tinytapeout.com) for enabling open-source ASIC development
* [YosysHQ](https://yosyshq.net/) for open-source synthesis tools
* [Icarus Verilog](http://iverilog.icarus.com/) for simulation
* [GTKWave](http://gtkwave.sourceforge.net/) for waveform viewing
* The open-source hardware community ❤️

---

## 📧 Contact

Author: **Sruthi192005**
GitHub: [@Sruthi192005](https://github.com/Sruthi192005)

---
