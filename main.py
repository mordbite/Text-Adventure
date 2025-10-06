import os 			# for cls 
import sys			# for sys.exit and sys.stdout.flush
import shutil		# for terminal size

"""
! PROGRESS BAR CALCULATION CURRENTLY BROKEN !

TODO: 
- Fix progress bar calculation
	- Possible fixes:
		1. Track visited chapters and calculate progress based on unique visits.
		2. Only Count Main Progression Chapters
	  	3. shortest path algorithm to end chapter after each choice and calculate progress based on that
- Implement save/load functionality
- Add error handling for file operations
- Improve text parsing to handle edge cases
- Enhance user interface for better experience (fancy borders, colors, etc.)

"""


# ------------------------------------------------------------
# Terminal Utilities
# ------------------------------------------------------------

def clear_terminal() -> None:
	os.system('cls' if os.name == 'nt' else 'clear')


# ------------------------------------------------------------
# Data Structures
# ------------------------------------------------------------

class ScreenContent:
	def __init__(self, progress_bar: str, content_lines: list[str], choice_map: dict[int, str]):
		self.progress_bar = progress_bar
		self.content_lines = content_lines
		self.choice_map = choice_map

	def print(self) -> int:
		terminal_height = shutil.get_terminal_size((80, 24)).lines - 10
		page_count = len(self.content_lines) // max(terminal_height, 1) + 1

		# --- Content Display ---
		for page_index in range(page_count):
			sys.stdout.flush()
			clear_terminal()
			print(f"{self.progress_bar}\n", flush=True)

			page_start = page_index * terminal_height
			page_end = page_start + terminal_height
			for line in self.content_lines[page_start:page_end]:
				print(line)

			if page_index < page_count - 1:
				print("\n")
				input("Press Enter to continue...")

		print("\n")

		# --- Choice Display ---
		if self.choice_map:
			first_iteration = True
			choice_input_text = "Choice: "
			while True:
				# Nur beim ersten Durchlauf clearen, wenn vorher kein Page-Clear kam
				if not first_iteration or page_count > 1:
					clear_terminal()
					print(f"{self.progress_bar}\n", flush=True)
				else:
					first_iteration = False

				for choice_id, choice_text in self.choice_map.items():
					if not choice_text:
						print("\n")
						input("Press Enter to continue...")
						return choice_id
					print(f"\n\t{choice_id}: {choice_text}")

				print("\n")
				choice_input = input(choice_input_text)
				if choice_input.isdigit() and int(choice_input) in self.choice_map:
					return int(choice_input)
				choice_input_text = "Invalid choice. Please try again: "

		return 0



class Chapter:
	"""Represents a story chapter with ID, title, text and available choices."""
	def __init__(self, chapter_id: int, title: str, content_lines: list[str], choice_map: dict[int, str]):
		self.id = chapter_id
		self.title = title
		self.content_lines = content_lines
		self.choice_map = choice_map


# ------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------

def read_file_as_string(file_path: str) -> str:
	"""Reads a UTF-8 encoded text file and returns its contents."""
	if not os.path.isfile(file_path):
		print(f"File '{file_path}' does not exist.")
		sys.exit(1)

	with open(file_path, "r", encoding="utf-8") as file:
		return file.read()


def split_sentences_preserving_quotes(full_text: str) -> list[str]:
	"""Splits text into sentences while respecting quoted text."""
	merged_text = ""
	is_inside_quotes = False

	for character in full_text:
		if character == '"':
			is_inside_quotes = not is_inside_quotes
		if character == "\n" and is_inside_quotes:
			continue
		merged_text += character

	sentences = []
	current_sentence = ""
	is_inside_quotes = False

	for index, character in enumerate(merged_text):
		current_sentence += character

		if character == '"':
			is_inside_quotes = not is_inside_quotes
		elif character in ".!?" and not is_inside_quotes:
			next_character = merged_text[index + 1] if index + 1 < len(merged_text) else ""
			if next_character not in ".!?":
				sentences.append(current_sentence.strip())
				current_sentence = ""

	if current_sentence.strip():
		sentences.append(current_sentence.strip())

	return sentences


def parse_chapter_text(chapter_id: int, chapter_title: str, raw_lines: list[str]) -> Chapter | None:
	"""Converts a section of text into a Chapter object."""
	full_text = "\n".join(raw_lines).strip()
	if not full_text:
		return None

	sentences = split_sentences_preserving_quotes(full_text)
	content_lines: list[str] = []
	choice_map: dict[int, str] = {}

	for sentence in sentences:
		trimmed_sentence = sentence.strip()
		if trimmed_sentence.startswith(">"):
			choice_parts = trimmed_sentence.split(">")
			if len(choice_parts) > 2 and choice_parts[1].isdigit():
				choice_id = int(choice_parts[1])
				choice_text = ">".join(choice_parts[2:]).strip()
				choice_map[choice_id] = choice_text
		else:
			content_lines.append(trimmed_sentence)

	return Chapter(chapter_id, chapter_title.strip(), content_lines, choice_map)


def parse_text_to_chapters(full_text: str) -> list[Chapter]:
	"""Parses the entire text input into a list of Chapter objects."""
	chapters: list[Chapter] = []
	text_lines = full_text.splitlines()

	current_chapter_id: int | None = None
	current_chapter_title: str = ""
	current_chapter_lines: list[str] = []

	for line in text_lines:
		trimmed_line = line.strip()

		if trimmed_line.startswith("###") and trimmed_line.endswith("###"):
			# Store previous chapter if one exists
			if current_chapter_id is not None:
				chapter = parse_chapter_text(current_chapter_id, current_chapter_title, current_chapter_lines)
				if chapter:
					chapters.append(chapter)

			# Extract ID and title
			line_parts = trimmed_line.strip("# ").split()
			current_chapter_id = next((int(part) for part in line_parts if part.isdigit()), None)
			current_chapter_title = " ".join(part for part in line_parts if not part.isdigit())
			current_chapter_lines = []

		else:
			current_chapter_lines.append(line)

	# Final chapter
	if current_chapter_id is not None:
		chapter = parse_chapter_text(current_chapter_id, current_chapter_title, current_chapter_lines)
		if chapter:
			chapters.append(chapter)

	return chapters


def calculate_progress_percentage(chapter_list: list[Chapter], current_index: int) -> float:
	"""Calculates current progress as a percentage."""
	total_chapter_count = len(chapter_list)
	return (current_index / total_chapter_count) * 100 if total_chapter_count > 0 else 0.0


def generate_progress_bar(percentage: float) -> str:
	"""Creates a visual progress bar string."""
	bar_length = os.get_terminal_size().columns - 20
	filled_length = int(bar_length * percentage // 100)
	progress_bar = "█" * filled_length + "░" * (bar_length - filled_length)
	return f"[{progress_bar}] {percentage:.2f}%"


# ------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------

def main() -> None:
	full_text = read_file_as_string("lines.txt")
	chapters = parse_text_to_chapters(full_text)
	clear_terminal()

	if not chapters:
		print("No chapters found.")
		sys.exit(1)

	next_chapter_id = chapters[0].id
	chapter_index = 0

	while True:
		current_chapter = next((chapter for chapter in chapters if chapter.id == next_chapter_id), None)
		if not current_chapter:
			print(f"Chapter with ID {next_chapter_id} not found. Exiting.")
			break

		clear_terminal()
		progress_percentage = calculate_progress_percentage(chapters, chapter_index + 1)
		screen_content = ScreenContent(
			generate_progress_bar(progress_percentage),
			current_chapter.content_lines,
			current_chapter.choice_map
		)

		next_chapter_id = screen_content.print()
		chapter_index += 1


if __name__ == "__main__":
	main()
