
# texase

Texase is a textual user interface for ASE databases. Also known as a TUI (Terminal/Text User Interface) it allows you to quickly get an overview and navigate an ASE database.

Built with Textual


## Demo

Insert gif or link to demo


## Screenshots

![App Screenshot](https://via.placeholder.com/468x300?text=App+Screenshot+Here)


## Installation

Install texase with pip

```bash
  pip install texase
```
    
## License

[MIT](https://github.com/steenlysgaard/texase/blob/main/LICENSE)


## Usage/Examples

I use the database in ASE a lot. The command line interface =ase db= could slow me down a bit though when I wanted to check out the results of some calculations and then view a structure or get some output in another way. I would normally go:
- `ase db file.db`
- `ase db -L 0 file.db`
- `ase db -s energy file.db`
- `ase gui file.db@id=32`
Now I can just `texase file.db` and do all the (quick) navigation I want.

- Navigation
- Marking
- Filtering
- Viewing
- Saving as trajectory
- Exporting
- Add key value pair
- Adding/removing columns
- Deleting rows (maybe say no)
- More info
- Hitting q doesn't stop the server


## Badges

Add badges from somewhere like: [shields.io](https://shields.io/)

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/steenlysgaard/texase/blob/main/LICENSE)

