## ❱ PATRIOTIC

**PATRIOTIC** (<u>P</u>ervasive <u>A</u>nti-<u>T</u>ampering and anti-<u>R</u>epackaging for <u>IoT</u> for <u>I</u>ntegrated <u>C</u>-based Firmware) is the first solution aimed at making IoT firmware self-resistant against repackaging through the whole production and delivery process. 

PATRIOTIC support the protection of IoT firmware designed in C/C++ programming language. The methodology exploits the use of cryptographically obfuscated logic bombs  (CLB) to hide anti-tampering (AT) checks directly in the firmware code. 

The tool consists of two modules:

* CLB Injector. This module works directly on the firmware source code and is responsible for parsing the source code, detecting the  QCs,  and building CLBs.
* CLB   Protector.   This   module   processes   the   compiled IoT  firmware, and  it  is  responsible  for  computing  the signature-verification digests of AT checks and encrypting the CLBs

## ❱ Publication

More details can be found in the paper
"[TODO](https://arxiv.org/abs/2012.09292)".

We submit it for consideration to [IEEE Internet of Things Journal](https://ieee-iotj.org).

<!--You can cite the paper as follows:
```BibTeX
@misc{XXX,
      title={TODO}, 
      author={Luca Verderame, Antonio Ruggia and Alessio Merlo},
      year={2021},
      eprint={XXXXX},
      archivePrefix={arXiv},
      primaryClass={cs.CR}
}
```-->

## ❱ Repo Structure

* In the `Tools` folder, you can find the source code of the *CLB Injector* and the *CLB Protector* projects.
* In the `Example` folder, you can find an usage example and the instruction to reproduce it.

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
