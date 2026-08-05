from pathlib import Path
from paddleocr import PPStructureV3
import pprint

pipeline = PPStructureV3(lang="en")

BASE_DIR = Path(__file__).resolve().parent
image_path = BASE_DIR / "med.jpg"

# results = pipeline.predict(str(image_path))

# print(type(results))
# print(len(results))

# res = results[0]

# print("\n========== JSON TYPE ==========")
# print(type(res.json))

# print("\n========== JSON ==========")
# pprint.pp(res.json)

# print("\n========== MARKDOWN TYPE ==========")
# print(type(res.markdown))

# print("\n========== MARKDOWN ==========")
# pprint.pp(res.markdown)

# print("\n========== ATTRIBUTES ==========")
# print(dir(res))


from paddleocr import PPStructureV3

pipeline = PPStructureV3()
# pipeline = PPStructureV3(lang="en") # Set the lang parameter to use the English text recognition model. For other supported languages, see Section 5: Appendix. By default, both Chinese and English text recognition models are enabled.
# pipeline = PPStructureV3(use_doc_orientation_classify=True) # Use use_doc_orientation_classify to enable/disable document orientation classification model
# pipeline = PPStructureV3(use_doc_unwarping=True) # Use use_doc_unwarping to enable/disable document unwarping module
# pipeline = PPStructureV3(use_textline_orientation=True) # Use use_textline_orientation to enable/disable textline orientation classification model
# pipeline = PPStructureV3(device="gpu") # Use device to specify GPU for model inference
output = pipeline.predict(image_path)
for res in output:
    res.print()  ## Print the structured prediction output
    res.save_to_json(
        save_path="output"
    )  ## Save the current image's structured result in JSON format
    res.save_to_markdown(
        save_path="output"
    )  ## Save the current image's result in Markdown format
    res.save_to_word(
        save_path="output"
    )  ## Save the current image's result in Word format
