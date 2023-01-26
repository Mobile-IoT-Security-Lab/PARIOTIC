## ❱ PARIOTIC

**PARIOTIC** (<u>P</u>ervasive <u>A</u>nti-<u>R</u>epackaging for <u>IoT</u> for <u>I</u>ntegrated <u>C</u>-based Firmware) is the first solution aimed at making IoT firmware self-resistant against repackaging through the whole production and delivery process. 

PATRIOTIC support the protection of IoT firmware designed in C/C++ programming language. The methodology exploits the use of cryptographically obfuscated logic bombs  (CLB) to hide anti-tampering (AT) checks directly in the firmware code. 

The tool consists of two modules:

* *CLB Injector*. This module works directly on the firmware source code and is responsible for parsing the source code, detecting the  QCs,  and building CLBs.
* *CLB   Protector*.   This   module   processes   the   compiled IoT  firmware, and  it  is  responsible  for  computing  the signature-verification digests of AT checks and encrypting the CLBs

## ❱ Publication

More details can be found in the paper
"[PARIOT: Anti-Repackaging for IoT Firmware](https://arxiv.org/abs/2109.04337)".

We submit it for consideration to [Computers & Security Journal](https://www.journals.elsevier.com/computers-and-security).

You can cite the paper as follows:
```BibTeX
@misc{https://doi.org/10.48550/arxiv.2109.04337,
  doi = {10.48550/ARXIV.2109.04337},
  url = {https://arxiv.org/abs/2109.04337},
  author = {Verderame, Luca and Ruggia, Antonio and Merlo, Alessio},
  keywords = {Cryptography and Security (cs.CR), FOS: Computer and information sciences, FOS: Computer and information sciences},
  title = {Anti-Repackaging for IoT Firmware Integrity},
  publisher = {arXiv},
  year = {2021},
  copyright = {arXiv.org perpetual, non-exclusive license}
}
```

## ❱ Licencing
This tool is available under a dual license: a commercial one required for closed source projects or commercial projects, and an AGPL license for open-source projects.

Depending on your needs, you must choose one of them and follow its policies. A detail of the policies and agreements for each license type is available in the [LICENSE.COMMERCIAL](LICENSE.COMMERCIAL) and [LICENSE](LICENSE) files.

## ❱ Credits

[![Unige](https://intranet.dibris.unige.it/img/logo_unige.gif)](https://unige.it/en/)
[![Dibris](https://intranet.dibris.unige.it/img/logo_dibris.gif)](https://www.dibris.unige.it/en/)

This software was developed for research purposes at the Computer Security Lab
([CSecLab](https://csec.it/)), hosted at DIBRIS, University of Genoa.

## ❱ Team
* [Alessio Merlo](https://csec.it/people/alessio_merlo/) - Faculty Member
* [Antonio Ruggia](https://github.com/totoR13) - PhD. Student
* [Luca Verderame](https://csec.it/people/luca_verderame/) - Postdoctoral Researcher
