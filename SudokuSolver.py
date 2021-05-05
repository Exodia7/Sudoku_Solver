
# For clearing screen
import os
# For determining which OS is used
import sys
# For saving/loading grids
import csv


# Define a class for an Error of an unsolvable grid
class UnsolvableGridError(RuntimeError):
	def __init__(self, arg):
		self.args = arg



# Define a class representing a sudoku box
class SudokuCell():
	# Set what value represents empty cells (cells whose value is not known)
	DEFAULT_VALUE = 0

	def __init__(self, value = DEFAULT_VALUE):
		""" Initialize this cell's value.
			
			Parameters:
			- value: the value that should be assigned to this cell.
				If it is equal to DEFAULT_VALUE, then the cell's value is considered unknown
				--> we keep track of all possible values
		"""
		# Save the value that it is given, to be able to determine whether the value is definitive or not
		self._value = value
		
		# Create the list of possible/impossible values
		if self.is_value_certain():
			self._possible = [self._value]
			self._impossible = [x for x in range(9) if x not in self._possible]
		if not self.is_value_certain():
			self._possible = list(range(1, 10))
			self._impossible = []
	
	@classmethod
	def get_default_value(cls):
		""" Getter for the default value of the cells """
		return cls.DEFAULT_VALUE
	
	@classmethod
	def is_default_value(cls, value):
		""" Checks whether the given value is the value assigned by default.
			
			Note that if a cell has a value other than the default value, 
			it means that its value is known for sure, 
			and if it has the same value, its value (in the grid) is not determined.
			
			Parameters:
			- value: the value to check
		"""
		return value == cls.get_default_value()
	
	def get_value(self):
		""" Getter for the 'value' field. """
		return self._value
	
	def set_value(self, value):
		""" Setter for the 'value' field. 
		
			Parameters:
			- value: the new value to assign this cell to
		"""
		self._value = value
	
	def is_value_possible(self, value):
		""" Checks whether the given value is still possible for this cell. """
		return value in self._possible
	
	def reset_value(self):
		""" Reset the value to the defaut value. """
		self.set_value(self.get_default_value())
	
	def is_value_certain(self):
		""" Returns whether we know this cell's value for sure. """
		return not self.is_default_value(self.get_value())
	
	def can_value_be_determined(self):
		""" Check and return whether the value of the cell can be determined for sure. 
			
			Note that it checks in the list of possible values, and not
		"""
		# If we know the value, we can not determine it anymore
		if self.is_value_certain():
			return False
		# Else, if there is only one possible number left
		elif len(self._possible) == 1:
			# We know the value of this cell for sure
			self.set_value(self._possible[0])
			return True
		# Else, if the cell has no possible values, the grid is unsolvable
		elif len(self._possible) == 0:
			raise UnsolvableGridError("This grid cannot be solved!")
		# Otherwise, we have multiple possible values
		else:
			return False
	
	def set_value_to_impossible(self, value):
		""" Set the given value as impossible for this cell.
		
			Parameters:
			- value: the value (in 1-9) that this cell can not take on
		"""
		# If this gives us a new hint,
		if value in self._possible:
			self._possible.remove(value)
			
			# Add the item at the correct index to keep the list sorted
			index = 0
			while index < len(self._impossible) and value > self._impossible[index]:
				index += 1
			
			self._impossible.insert(index, value)
	
	def eliminate_conflicting_values(self, other):
		""" Eliminate possible values by the value of the other cell. 
		
			Given the other cell, we make sure that one of this cell or the other are uncertain.
			{ If both are uncertain, we can hardly gain information [BORDERLINE CASE, COULD BE ADDED LATER],
			  If both are certain, we do not gain any information (unless the grid is infeasible)
			}
			
			Parameters:
			- other: the other cell conflicting with this cell 
				(meaning that this cell and 'other' can not have the same value)
			
			Returns:
			whether we know a new cell value for sure
		"""
		# Check whether it is a valid case
		information_can_be_deduced = False
		
		# Compute whether the cells' value is certain
		self_is_certain = self.is_value_certain()
		other_is_certain = other.is_value_certain()
		
		# Save the cells in other variables
		if self_is_certain and not other_is_certain:			# Case 1: self has certain value, other is uncertain
			information_can_be_deduced = True
			certain_cell = self
			uncertain_cell = other
		elif not self_is_certain and other_is_certain:			# Case 2: self has uncertain value, other is certain
			information_can_be_deduced = True
			certain_cell = other
			uncertain_cell = self
		
		if information_can_be_deduced:
			# Then, set the value of the certain cell to impossible in the uncertain cell
			uncertain_cell.set_value_to_impossible(certain_cell.get_value())
			# And return whether the value can now be determined for sure
			return uncertain_cell.can_value_be_determined()
		else:
			# No new information
			return False
	
	def clone(self):
		""" Create a duplicate of this cell. """
		cloned = SudokuCell(self.get_value())
		
		return cloned



# Define a class representing the whole sudoku grid
class SudokuGrid():
	def __init__(self, custom_unk_symb = ''):
		""" Initialize this Sudoku Grid.
			
			Parameters:
			- custom_unk_symb: the symbol used for representing cells with unknown value.
				If it is None or '' (empty string), then ' ' (space) is used by default
		"""
		# Create a default grid of cells and matrix of same size for whether we used that cell's value to extract information yet
		self._grid = [[SudokuCell() for i in range(9)] for j in range(9)]
		self._used_cell = [[False for i in range(len(self._grid[0]))] for j in range(len(self._grid))]
		
		# Set a custom symbol for representing empty cells.
		self._custom_unknown_cell_symbol = custom_unk_symb
	
	def __getitem__(self, key):
		""" Used for accessing specific items of the grid via indexing.
			
			Parameters:
			- key: the index of the item to retrieve
			
			Returns:
			the <key>th row of the grid
		"""
		return self._grid[key]
	
	def get_unknown_symbol(self):
		""" Return the symbol used for indicating cells of unknown value.
			
			If the _custom_unknown_cell_symbol field is None or the empty string, we use the default symbol space,
			Otherwise, we use the symbol itself
		"""
		custom_symb = self._custom_unknown_cell_symbol
		return ' ' if (custom_symb == None or custom_symb == '') else custom_symb
	
	@classmethod
	def create_from_matrix(cls, matrix):
		""" Returns a SudokuGrid object based on the given matrix grid. 
		
			Note that the grid should use the same DEFAULT_VALUE parameter as in SudokuCell
			for indicating cells with unknown value.
			
			Parameters:
			- matrix: the integer matrix that we should use to create the new SudokuGrid
		"""
		# Create a new empty SudokuGrid
		grid = SudokuGrid()
		
		# Then, set all cells' values to the value in the grid
		for i in range(len(matrix)):
			for j in range(len(matrix[0])):
				grid[i][j].set_value(matrix[i][j])
		
		# Return the filled out grid
		return grid
	
	def get_as_matrix(self):
		""" Returns this grid as a matrix (list of lists of integers). """
		# Create a matrix of only -1's
		matrix = [[-1 for i in range(9)] for j in range(9)]
		
		# Go through the grid, copying the cell's values
		for i in range(len(self._grid)):
			for j in range(len(self._grid[0])):
				matrix[i][j] = self._grid[i][j].get_value()
		
		# And return the copy
		return matrix
	
	def get_square_code(self, row, column):
		""" Identify which main square the cell at the position determined by the specified row and column is in. 
		
			The codes are assigned such as to have the following subdivision of the grid:
				   | 1 | 2 | 3 || 4 | 5 | 6 || 7 | 8 | 9 |
				---------------------------------------------------
				 A |           ||           ||           |
				----           --           --           -
				 B | Square 0  || Square 1  || Square 2  |   TOP
				----           --           --           -
				 C |           ||           ||           |
				---------------------------------------------------
				---------------------------------------------------
				 D |           ||           ||           |
				----           --           --           -
				 E | Square 3  || Square 4  || Square 5  |   MID
				----           --           --           -
				 F |           ||           ||           |
				---------------------------------------------------
				---------------------------------------------------
				 G |           ||           ||           |
				----           --           --           -
				 H | Square 6  || Square 7  || Square 8  |  BOTTOM
				----           --           --           -
				 I |           ||           ||           |
				---------------------------------------------------
				   |           ||           ||           |
				   |   LEFT    ||    MID    ||   RIGHT   |
				   |           ||           ||           |
			
			Parameters:
			- row: the row of the cell whose square should be computed
			- column: the column of the cell whose square should be computed
		"""
		# Determine if we are in the top, mid or bottom vertical part
		if row <= 2:
			horizontal_num = 0
		elif row <= 5:
			horizontal_num = 1
		else:
			horizontal_num = 2
		
		# Identify if we are in the left, mid or right horizontal part
		if column <= 2:
			vertical_num = 0
		elif column <= 5:
			vertical_num = 1
		else:
			vertical_num = 2
		
		# Compute the code using that information
		square_code = horizontal_num*3 + vertical_num
		
		return square_code
	
	def get_square_cells(self, square_code):
		""" Return all cells inside the square of given code. 
			
			Parameters:
			- square_code: the code of the square whose cells should be returned
		"""
		# Retrieve the vertical and horizontal code
		horizontal_num = square_code % 3
		vertical_num = (square_code - horizontal_num) // 3
		
		# For each cell in the given square, add it to the resulting list
		result = []
		for row in range(vertical_num * 3, (vertical_num+1) * 3):
			for column in range(horizontal_num*3, (horizontal_num+1) * 3):
				result.append(self._grid[row][column])
		
		# Return the list
		return result
	
	def is_solved(self):
		""" Return whether the grid is fully solved or not. """
		solved = True
		index = 0
		while solved and index < len(self._grid)*len(self._grid[0]):
			# Extract the row and column
			column = index % len(self._grid[0])
			row = (index - column) // len(self._grid[0])
			
			# Check the cell
			if not self._grid[row][column].is_value_certain():
				if not self._grid[row][column].can_value_be_determined():
					solved = False
			else:
				index += 1
		
		return solved
	
	def show(self, show_coords=True, spaces_before=5):
		""" Print the grid in a nicely formatted manner. 
		
			By default, show_coords is False, and we print the grid like this:
				---------------------------------------
				|   |   |   ||   |   |   ||   |   |   |
				---------------------------------------
				|   |   |   ||   |   |   ||   |   |   |
				---------------------------------------
				|   |   |   ||   |   |   ||   |   |   |
				---------------------------------------
				---------------------------------------
				|   |   |   ||   |   |   ||   |   |   |
				---------------------------------------
				|   |   |   ||   |   |   ||   |   |   |
				---------------------------------------
				|   |   |   ||   |   |   ||   |   |   |
				---------------------------------------
				---------------------------------------
				|   |   |   ||   |   |   ||   |   |   |
				---------------------------------------
				|   |   |   ||   |   |   ||   |   |   |
				---------------------------------------
				|   |   |   ||   |   |   ||   |   |   |
				---------------------------------------
			
			where double lines are used to delimit big squares.
			
			
			But, when show_coords is set to True, it will print the coordinates for the cells:
				   | 1 | 2 | 3 || 4 | 5 | 6 || 7 | 8 | 9 |
				------------------------------------------
				 A |   |   |   ||   |   |   ||   |   |   |
				------------------------------------------
				 B |   |   |   ||   |   |   ||   |   |   |
				------------------------------------------
				 C |   |   |   ||   |   |   ||   |   |   |
				------------------------------------------
				------------------------------------------
				 D |   |   |   ||   |   |   ||   |   |   |
				------------------------------------------
				 E |   |   |   ||   |   |   ||   |   |   |
				------------------------------------------
				 F |   |   |   ||   |   |   ||   |   |   |
				------------------------------------------
				------------------------------------------
				 G |   |   |   ||   |   |   ||   |   |   |
				------------------------------------------
				 H |   |   |   ||   |   |   ||   |   |   |
				------------------------------------------
				 I |   |   |   ||   |   |   ||   |   |   |
				------------------------------------------
			
			
			Moreover, the parameter spaces_before can be used to indent the whole grid as many spaces to the right
		"""
		# Compute the string of the spaces that should be added before each line to indent the grid by as many spaces
		indent = ' ' * spaces_before
		# Like this:
		#print(indent, end='')
		
		# If we should show the coordiantes, we need to print the column's coordinates
		if show_coords:
			# we need to print the column coordinates
			print(indent, end='')
			print('   | 1 | 2 | 3 || 4 | 5 | 6 || 7 | 8 | 9 |')
		
		for square_row in range(len(self._grid)//3):
			# Print the line before each inner row of squares
			if square_row != 0:
				# Print the indent before the coming line
				print(indent, end='')
				
				# If we should show the coordinates,
				if show_coords:
					# add 2 tiles to every line
					print('---', end='')
				
				print('---------------------------------------')
			
			for cell_row in range(3):
				# Compute the number of rows
				row = square_row * 3 + cell_row
				
				# Print the indent before the coming line
				print(indent, end='')
				
				# Print the line before each row
				if show_coords:
					print('---', end='')
				print('---------------------------------------')
				# The row should look sth like this:
				# print('| 3 | 4 | 5 || 6 | 7 | 8 || 8 | 9 | 1 |') (with all cells having values)
				
				# Print the indent before the coming line
				print(indent, end='')
				
				# If we should show the coordinates,
				if show_coords:
					# Print the row letter as well
					print(f' {chr(65+row)} ', end='')
				
				# Print the whole row
				for square_column in range(len(self._grid[row])//3):
					print('|', end='')
					for cell_column in range(3):
						# Compute the number of columns
						column = square_column * 3 + cell_column
						
						# Compute the number of that cell
						number = self._grid[row][column].get_value()
						print(f" {number if (self._grid[row][column].is_value_certain()) else self.get_unknown_symbol()} |", end='')
				
				# Print a newline
				print()
		
		# Print the indent before the coming line
		print(indent, end='')
		
		# And print a line after the last row
		if show_coords:
			print('---', end='')
		print('---------------------------------------')
	
	def solve(self):
		""" Attempt to resolve the complete Grid. 
		
			For this, we can use the following information:
				- in a given row, all numbers from 1-9 should only appear once
				- in a given column, all numbers from 1-9 should only appear once
				- in a square of 3x3 (top/mid/bottom and left/mid/right), all numbers from 1-9 should only appear once
		"""
		# As long as we determine the value of new cells and the grid is not solved,
		number_new_determined = -1
		number_iterations = 0
		while (number_new_determined != 0) and not self.is_solved():
			number_iterations += 1
			
			number_new_determined = 0
			
			# Go through the whole grid searching for cells of determined value
			for row in range(len(self._grid)):
				for column in range(len(self._grid)):
					# Check if the cell has a certain value and has not yet been used to deduce information
					if self._grid[row][column].is_value_certain() and not self._used_cell[row][column]:
						# Update the list of possible values for all cells in the same row, column and square
						if DEBUG:
							self.show()
							input()
						
						update_row = row
						update_column = column
						update_square_code = self.get_square_code(row, column)
						comparison_cell = self._grid[row][column]
						
						### DEBUGGING ###
						if DEBUG:
							print(f'Using cell at coordinates ({update_row}, {update_column}):')
						# For all cells in the same row and same column
						for k in range(len(self._grid)):
							''' NOTE: WE ASSUME THAT THE GRID IS SQUARE HERE '''
							# Check for the other cells in the same row
							if (k != update_column and not self._grid[update_row][k].is_value_certain()):
								# Update value of self._grid[update_row][k]
								deduced_new_cell = self._grid[update_row][k].eliminate_conflicting_values(comparison_cell)
								if DEBUG:
									print(f'Using information on cell ({update_row}, {k}) gives new certain cell: {deduced_new_cell}')
									if deduced_new_cell:
										input()
								
								number_new_determined += deduced_new_cell
								# while keeping track of the number of new cells that become determined
							
							# Check for the other cells in the same column
							if (k != update_row and not self._grid[k][update_column].is_value_certain()):
								# Update value of self._grid[k][update_column]
								deduced_new_cell = self._grid[k][update_column].eliminate_conflicting_values(comparison_cell)
								if DEBUG:
									print(f'Using information on cell ({k}, {update_column}) gives new certain cell: {deduced_new_cell}')
									if deduced_new_cell:
										input()
									
								number_new_determined += deduced_new_cell
								# while keeping track of the number of new cells that become determined
						
						# Then, go through all cells in the square
						square_cells = self.get_square_cells(update_square_code)
						if DEBUG:
							print(f'Square is square with code {update_square_code}, \nwith cells: {square_cells}')
						for i in range(len(square_cells)):
							if (square_cells[i] != self._grid[update_row][update_column]) and not square_cells[i].is_value_certain():
								# Update that item
								deduced_new_cell = square_cells[i].eliminate_conflicting_values(comparison_cell)
								number_new_determined += deduced_new_cell
								# while keeping track of the number of new cells that become determined
								if DEBUG:
									print(f'Using information on cell with value {square_cells[i].get_value()} gives new certain cell: {bool(deduced_new_cell)}')
									if deduced_new_cell:
										input()
						
						# Update the matrix of whether the cell was used for the é
						self._used_cell[row][column] = True
			
			# Check if there is a square in which there is a value which only 1 cell could possibly have
			for square_code in range(9):
				square_cells = self.get_square_cells(square_code)
				# Determine the values that do not yet have a certain cell
				certain_values = [x for x in range(1,10) if x in [cell.get_value() for cell in square_cells]]
				values_to_check = [i for i in range(1, 10) if i not in certain_values]

				# Go over all these values, and check how many cells it can possibly be in
				for value in values_to_check:
					possible_cells = []
					cell_index = 0
					while cell_index < len(square_cells) and len(possible_cells) < 2:
						if square_cells[cell_index].is_value_possible(value):
							possible_cells.append(square_cells[cell_index])
						
						cell_index += 1
					
					# If there is a single cell in the square that can have that value, we have a newly determined cell
					
					if len(possible_cells) == 1:
						possible_cells[0].set_value(value)
						number_new_determined += 1
						if DEBUG:
							print(f'Managed to find a new value by checking for single possible values in big squares.')
					# But if that value has no possible cell, then we're fucked
					elif len(possible_cells) == 0:
						raise UnsolvableGridError("This grid cannot be solved!")
					
					
		
		# Return the result
		return self.is_solved()
	
	def set_value(self, row, col, value):
		""" Sets the value of the cell at the specified row and column to the given value. """
		self._grid[row][col].set_value(value)
	
	def clone(self):
		""" Create a duplicate of this grid. """
		# Create a new empty grid
		cloned = SudokuGrid(self._custom_unknown_cell_symbol)
		
		# Copy all cell's values into the new grid
		for i in range(len(self._grid)):
			for j in range(len(self._grid[i])):
				cloned[i][j] = self._grid[i][j].clone()
		
		return cloned





class SudokuSolverUI():
	def __init__(self, custom_unk_symb = '', grid_folder = '.\\Grids'):
		""" Initialize the variables.
		
			Parameters:
			- custom_unk_symbol: the symbol to use for empty cells.
				If it is None or the empty string, the empty cells will be displayed as empty.
			- grid_folder: the folder in which to save/load grids
		"""
		# Add the possibility to run it from my linux machine
		if sys.platform not in ['win32', 'cygwin']:
			grid_folder = './Grids'
		
		self._custom_unknown_cell_symbol = custom_unk_symb
		self._grid = SudokuGrid(self._custom_unknown_cell_symbol)
		self.grid_directory = grid_folder
	
	def intro(self):
		""" Prints the introduction to the Sudoku Solver. """
		print(f"Welcome to the Sudoku Solver{chr(169)} User Interface")
		print("This program can be used to create, save, load and resolve Sudoku grids.")
		print("Follow the instructions below to continue.")
		input("Press enter to continue ...")
		print()
	
	def show_commands(self):
		""" Prints the possible commands. """
		print("Possible commands are:")
		print("    - '<Row Letter><Column Number> <Cell Value>")
		print("          Modifies the cell at the given row and column and set it to the given value.")
		print("    - 'load <file_name>'")
		print("          Loads the file at the given relative path.")
		print("    - 'save <file_name>'")
		print("          Saves the current grid at the given relative path.")
		print("    - 'solve'")
		print("          Attempts to solve the current grid")
		print("    - 'exit'")
		print("          Exits the User Interface and terminates the program.")
		print()
	
	def clear_screen(self):
		""" Clears the terminal's screen. """
		if sys.platform in ['win32', 'cygwin']:
			# For Windows
			os.system('cls')
		else:
			# For Linux and MacOS
			os.system('clear')
	
	def launch_menu(self):
		""" Launches the User interface displaying the different options. """
		# Start off with the intro
		self.intro()
		
		# Keep track of whether we continue looping
		terminate = False
		while not terminate:
			# Show the current grid
			print('Current grid: \n')
			self._grid.show()
			# Ask the User for a command
			instruction = input("Enter a command or 'help': ")
			print()
			
			# Check whether we have a valid input
			valid_input = True
			clear_screen = True
			
			# Interpret the output and act accordingly
			if len(instruction) < 4:					# It can't be a valid command, so we reject it
				valid_input = False
				print("Please enter a valid command. \nNote that you can get an overview of the commands by entering the command 'help'\n")
			if instruction.lower() == 'help':			# Show the possible commands
				self.show_commands()
				clear_screen = False
			elif instruction.lower() == 'exit':			# Terminate the program
				terminate = True
				clear_screen = False
			elif instruction.lower() == 'solve':		# Try to solve the current grid
				# Try to solve the grid
				try:
					# Clone the grid such that the original grid stays the same, in case the User wants to change the starting grid later
					cloned_grid = self._grid.clone()
					success = cloned_grid.solve()
					
					# Show the grid as far as we managed to solve it
					cloned_grid.show()
					# And conclude on the success of the resolution
					print('Successfully managed to completely resolve grid.\n' if success else "\nDidn't manage to fully resolve the grid.\n")
				except UnsolvableGridError:
					# Show the grid and conclude that the grid is unsolvable
					cloned_grid.show()
					print('Grid is unsolvable for this algorithm...\n')
				
				input('Press enter to continue...')
				
				clear_screen = False
			elif instruction.lower()[:5] == 'save ':		# Save the current grid
				file_name = instruction[5:]
				success = self.save_grid(file_name, self._grid)
				print(f'Successfully saved grid to file named "{file_name}".\n' if success else f'\nError when saving grid to file named "{file_name}".\n')
				input('Press enter to continue')
			elif instruction.lower()[:5] == 'load ':		# Load a grid
				file_name = instruction[5:]
				success = self.load_grid(file_name)
				print(f'Successfully loaded grid from file named "{file_name}".\n' if success else f'\nError when loading grid to file named "{file_name}".\n')
				input('Press enter to continue')
			elif len(instruction) == 4:						# We try to match'<Row Letter><Column Number> <Cell Value>'
				# Keep track of whether it is valid
				valid_input = False
				try:
					# Try reading the items (and converting the supposed integers to integers)
					data = instruction.split()
					if len(data) != 2 or len(data[0]) != 2 or len(data[1]) != 1:
						# Doesn't match the format, but length does not match, so the User could also mean another command
						valid_input = False
						print("Please make sure to enter a valid command. Alternatively, enter 'help' for a display of possible commands\n")
					else:
						row = data[0][0].upper()
						column = int(data[0][1])
						value = int(data[1][0])
						# Mark the input as valid
						valid_input = True
				except ValueError:
					# An integer conversion raised an exception of invalid value for integer
					print('Please make sure to enter a valid integer value for the column and cell value\n')
				
				# If the input has the correct format, verify that their values are valid
				if valid_input:
					# Make sure the row is in 'A'-'I', the column is in 1-9 and the value is in 0-9
					valid_row = (row >= 'A') and (row <= 'I')
					valid_column = (column >= 1) and (column <= 9)
					valid_value = (value >= 0) and (value <= 9)
					
					# And only stop the loop if all entries are valid
					valid_input = valid_row and valid_column and valid_value
					
					if valid_input:
						# If the input is still valid, modify the cell's value
						index_row = ord(row) - 65
						index_col = column - 1
						self._grid.set_value(index_row, index_col, value)
					else:
						if not valid_row:
							print('Please enter a letter from "A" to "I" for the row')
						elif not valid_column:
							print('Please enter a number between 1 and 9 for the column')
						else:
							print('Please enter a number between 0 and 9 for the value')
			
			# If it was a valid command, we have executed it and clear the screen again
			if valid_input and clear_screen:
				# Clear the screen
				self.clear_screen()
	
	def get_path_separator(self):
		""" Returns the path separator for the given platform.
			Supported platforms:
			- Windows: separator = '\\'
			- Linux: separator = '/'
		"""
		if sys.platform in ['win32', 'cygwin']:
			return '\\'
		else:
			return '/'
	
	def save_grid(self, file_name, grid):
		""" Saves the given grid to the file name, in the folder set in the constructor.
		
			Parameters:
			- file_name (str): the name under which to save the grid
			- grid (SudokuGrid object): the grid to save
			
			Returns whether the saving was successful or not
		"""
		success = True
		# If there is any error, we return False
		try:
			# Complete the file name if necessary:
			file_name = self.complete_file_name(file_name)
			
			# Then save it
			with open(self.grid_directory + self.get_path_separator() + file_name, mode='w', newline='') as grid_file:
				# Create the writer object
				grid_writer = csv.writer(grid_file)#, line_terminator='\n')
				
				# Extract the grid to a matrix
				grid_matrix = grid.get_as_matrix()
				
				# Then, write out the rows, one by one
				for row in range(len(grid_matrix)):
					grid_writer.writerow(grid_matrix[row])
		except:
			success = False
		
		return success
	
	def load_grid(self, file_name):
		""" Loads a grid from the given file name and saves it under self._grid
			
			Raises an exception in case the file is not formatted correctly, 
			according to the following rules:
			- at most 9 columns in the file
			- at most 9 rows in the file
			- all entries must be integer values
			
			Parameters:
			- file_name: the name of the file to load
			
			Returns whether the loading was successful or not
		"""
		success = True
		try:
			# Complete the file name if necessary
			file_name = self.complete_file_name(file_name)
			
			# Then load it
			with open(self.grid_directory + self.get_path_separator() + file_name, newline='') as grid_file:
				# Create the reader object
				grid_reader = csv.reader(grid_file)
				
				# Create a matrix to hold the values from the csv
				grid_matrix = [[-1 for i in range(9)] for j in range(9)]
				
				# Read all rows of the file
				for row in grid_reader:
					i = grid_reader.line_num - 1
					# Check that the line has at most 9 columns
					assert len(grid_matrix[i]) >= len(row), f'Invalid file! File {file_name} has more than 9 columns!'
					for j in range(len(row)):
						# Try setting the matrix's cell to the given integer value, 
						# and raise an error if 1. there are too many rows or 2. there are non-integers
						try:
							grid_matrix[i][j] = int(row[j])
						except ValueError:
							print(f'Invalid file! File {file_name} contains non-integer entries !')
						except IndexError:
							print(f'Invalid file! File {file_name} has more than 9 rows !')
				
				# Then, compute the SudokuGrid based on the matrix and return it
				grid = SudokuGrid.create_from_matrix(grid_matrix)
				
				self._grid = grid
		# If any exception happened, we were not successful
		except:
			success = False
		
		return success
	
	def complete_file_name(self, file_name):
		""" Complete the given file name if necessary for it to be a valid text file. """
		if '.' not in file_name:
			file_name = file_name + '.txt'
		
		return file_name



''' TODO:
	- add functionality to reset full grid
	- add possibility for step-by-step solution of the grid ?
'''



# Enable or disable step-by-step solving mode (DEBUG mode)
DEBUG = False



def main():
	# Set the symbol to use for unknown cells (if '' or None, it will be space by default [' '])
	unk_cell_symbol = ''
	
	# Create the sudoku grid
	menu = SudokuSolverUI(unk_cell_symbol)
	
	# Launch the menu
	menu.launch_menu()



if __name__ == "__main__":
    main()