import argparse
from contextlib import redirect_stdout
from datetime import date
from io import StringIO
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('crib_build', ROOT / 'scripts/build.py')
crib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crib)

class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source.md'
        self.source.write_text((ROOT / 'examples/crib-sheet.md').read_text())
        self.args = argparse.Namespace(source=self.source, out=self.root/'out', date='2026-09-06', timezone='UTC', paper='letter', widths=None, preview_only=False)

    def build(self):
        with redirect_stdout(StringIO()):
            crib.build(self.args)

    def hashes(self):
        return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.args.out.iterdir() if p.is_file()}

    def test_letter_pdf_preserves_recipes_and_omits_notes(self):
        self.build()
        from pypdf import PdfReader
        pdf = PdfReader(self.args.out/'crib-sheet.pdf')
        self.assertEqual(len(pdf.pages), 1)
        self.assertEqual(tuple(map(float, pdf.pages[0].mediabox)), (0,0,612,792))
        text = pdf.pages[0].extract_text()
        self.assertIn('September 6, 2026', text)
        self.assertNotIn('Source notes', text)
        self.assertEqual(len(pdf.pages[0].images), 8)
        self.assertTrue(all(img.image.mode == 'L' for img in pdf.pages[0].images))
        self.assertTrue(json.loads((self.args.out/'build.json').read_text())['pdf_validated'])

    def test_a4_and_variable_recipe_count(self):
        self.source.write_text('# My sheet\n<!-- recipes:start -->\n## Prep\n### Plain\n- Salt, ½t\n- Combined, ¾c\n- Unknown, TKoz\n<!-- recipes:end -->')
        self.args.paper='a4'
        self.build()
        from pypdf import PdfReader
        page=PdfReader(self.args.out/'crib-sheet.pdf').pages[0]
        self.assertAlmostEqual(float(page.mediabox.width), 595.276, places=2)
        self.assertIn('TKoz', page.extract_text())
        self.assertNotIn('Twemoji', page.extract_text())
        self.assertEqual(json.loads((self.args.out/'build.json').read_text())['recipe_count'],1)

    def test_failed_overflow_keeps_previous_outputs(self):
        self.build()
        before=self.hashes()
        source='# Too full\n<!-- recipes:start -->\n## Prep\n### Large\n' + '- Ingredient, 100g\n'*250 + '<!-- recipes:end -->'
        self.source.write_text(source)
        with self.assertRaisesRegex(ValueError, 'pages|printable'):
            self.build()
        self.assertEqual(before,self.hashes())

    def test_invalid_input_keeps_previous_outputs(self):
        self.build()
        before=self.hashes()
        self.source.write_text(self.source.read_text().replace('- Lemon juice, 1T','unrecognized block'))
        with self.assertRaisesRegex(ValueError,'Unsupported'):
            self.build()
        self.assertEqual(before,self.hashes())

    def test_preview_marks_old_pdf_as_stale(self):
        self.build()
        old=(self.args.out/'crib-sheet.pdf').read_bytes()
        self.source.write_text(self.source.read_text().replace('Lemon juice, 1T','Lemon juice, 2T'))
        self.args.preview_only=True
        self.build()
        self.assertEqual(old,(self.args.out/'crib-sheet.pdf').read_bytes())
        receipt=json.loads((self.args.out/'build.json').read_text())
        self.assertFalse(receipt['pdf_validated'])
        self.assertNotIn('crib-sheet.pdf',receipt['outputs'])
        self.assertIn('2T',(self.args.out/'crib-sheet.html').read_text())

    def test_escape_links_and_reject_unknown_icon(self):
        self.assertEqual(crib.inline('[[Book|Source]] <script>'), 'Source &lt;script&gt;')
        self.assertEqual(crib.inline('2 tsp'), '2\u00a0tsp')
        with self.assertRaisesRegex(ValueError,'No bundled icon'):
            crib.heading('🚀 Rockets')

    def test_all_bundled_icons_and_manifest(self):
        from weasyprint import HTML
        icons=json.loads((ROOT/'assets/emoji/manifest.json').read_text())['sha256']
        for filename,digest in icons.items():
            self.assertEqual(hashlib.sha256((ROOT/'assets/emoji'/filename).read_bytes()).hexdigest(),digest)
        source='# Icons\n<!-- recipes:start -->\n## Gallery\n'
        for i,filename in enumerate(icons):
            emoji=''.join(chr(int(x,16)) for x in filename[:-4].split('-'))
            source+=f'### {emoji} Icon {i}\n- A reminder\n'
        source+='<!-- recipes:end -->'
        fragment,_,_=crib.render(source,date(2026,9,6))
        doc=HTML(string=fragment).render()
        images=[b for p in doc.pages for b in p._page_box.descendants() if getattr(b,'element_tag','')=='img' and hasattr(b,'replacement')]
        self.assertEqual(len(images),len(icons))
        for img in images:
            self.assertAlmostEqual(img.width,11*96/72,places=3)
            self.assertAlmostEqual(img.height,11*96/72,places=3)

if __name__=='__main__':
    unittest.main()
