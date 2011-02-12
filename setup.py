"""Commands to build and manage .sublime-package archives with distutils."""

import os

from distutils.core import Command
from distutils.filelist import FileList
from distutils.text_file import TextFile
from distutils import dir_util, dep_util, file_util, archive_util
from distutils import log
from distutils.core import setup
from distutils.errors import *


class spa(Command):
	"""A command to make .sublime-packages out of directories containing
	Sublime Text resoures.
	"""
	
	description = "Creates a .sublime-package archive."
	user_options = [('no', 'n', 'no')]

	def run(self):
		self.file_list = FileList()

		# XXX: currently does nothing
		self.check_metadata()

		self.get_file_list()
		self.make_distribution()
			
	def initialize_options(self):
		pass
	
	def finalize_options(self):
		self.manifest_template = 'Manifest.sublime-package-manifest'
		self.manifest = 'Manifest'
		self.formats = ['zip']
		self.dist_dir = "dist"
		self.keep_temp = 0
	
	def check_metadata(self):
		pass
	
	def get_file_list(self):
		
		template_exists = os.path.exists(self.manifest_template)
		if not template_exists:
			assert False, "Missing manifest."

		self.file_list.findall()

		if template_exists:
			self.read_template()

		self.file_list.sort()
		self.file_list.remove_duplicates()
		self.write_manifest()
	
	def read_template(self):
		template = TextFile(self.manifest_template,
							strip_comments=1,
							skip_blanks=1,
							join_lines=1,
							lstrip_ws=1,
							rstrip_ws=1,
							collapse_join=1)

		while 1:
			line = template.readline()
			if line is None:			# end of file
				break

			try:
				self.file_list.process_template_line(line)
			except DistutilsTemplateError, msg:
				print "%s, line %d: %s" % (template.filename,
											   template.current_line,
											   msg)
	
	def write_manifest (self):
		"""Write the file list in 'self.filelist' (presumably as filled in
		by 'add_defaults()' and 'read_template()') to the manifest file
		named by 'self.manifest'.
		"""
		self.execute(file_util.write_file,
					 (self.manifest, self.file_list.files),
					 "writing manifest file '%s'" % self.manifest)

	def make_release_tree (self, base_dir, files):
		"""Create the directory tree that will become the source
		distribution archive.  All directories implied by the filenames in
		'files' are created under 'base_dir', and then we hard link or copy
		(if hard linking is unavailable) those files into place.
		Essentially, this duplicates the developer's source tree, but in a
		directory named after the distribution, containing only the files
		to be distributed.
		"""
		# Create all the directories under 'base_dir' necessary to
		# put 'files' there; the 'mkpath()' is just so we don't die
		# if the manifest happens to be empty.
		self.mkpath(base_dir)
		dir_util.create_tree(base_dir, files, dry_run=self.dry_run)
		# And walk over the list of files, either making a hard link (if
		# os.link exists) to each one that doesn't already exist in its
		# corresponding location under 'base_dir', or copying each file
		# that's out-of-date in 'base_dir'.  (Usually, all files will be
		# out-of-date, because by default we blow away 'base_dir' when
		# we're done making the distribution archives.)
		if hasattr(os, 'link'):		# can make hard links on this system
			link = 'hard'
			msg = "making hard links in %s..." % base_dir
		else:						   # nope, have to copy
			link = None
			msg = "copying files to %s..." % base_dir
		if not files:
			log.warn("no files to distribute -- empty manifest?")
		else:
			log.info(msg)
		for file in files:
			if not os.path.isfile(file):
				log.warn("'%s' not a regular file -- skipping" % file)
			else:
				dest = os.path.join(base_dir, file)
				self.copy_file(file, dest, link=link)
		self.distribution.metadata.write_pkg_info(base_dir)

	def make_distribution (self):
		"""Create the source distribution(s).  First, we create the release
		tree with 'make_release_tree()'; then, we create all required
		archive files (according to 'self.formats') from the release tree.
		Finally, we clean up by blowing away the release tree (unless
		'self.keep_temp' is true).  The list of archive files created is
		stored so it can be retrieved later by 'get_archive_files()'.
		"""
		# Don't warn about missing meta-data here -- should be (and is!)
		# done elsewhere.
		base_dir = self.distribution.get_fullname()
		base_name = os.path.join(self.dist_dir, base_dir)

		self.make_release_tree(base_dir, self.file_list.files)
		archive_files = []			  # remember names of files we create
		# tar archive must be created last to avoid overwrite and remove
		if 'tar' in self.formats:
			self.formats.append(self.formats.pop(self.formats.index('tar')))

		for fmt in self.formats:
			file = self.make_archive(base_name, fmt, base_dir=base_dir)
			archive_files.append(file)
			self.distribution.dist_files.append(('spa', '', file))

		self.archive_files = archive_files

		if not self.keep_temp:
			dir_util.remove_tree(base_dir, dry_run=self.dry_run)

	def get_archive_files (self):
		"""Return the list of archive files created when the command
		was run, or None if the command hasn't run yet.
		"""
		return self.archive_files


class install(Command):
	"""Does it make sense?"""

	user_options = [('aa', 'a', 'aa')]

	def initialize_options(self):
		pass
	
	def finalize_options(self):
		pass

	def run(self):
		print NotImplementedError("Command not implemented yet.")


setup(cmdclass={'spa': spa, 'install': install},
	  name='echo',
	  version='1.0',
	  description='Sublime Text .sublime-package packager.',
	  author='Guillermo Lopez-Anglada',
	  author_email='guillermo@sublimetext.info',
	  url='http://sublimetext.info',
	  py_modules=['echo']
	 )