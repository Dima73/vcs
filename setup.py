from distutils.core import setup
import setup_translate

setup(name='enigma2-plugin-extensions-vcs',
		version='2.2',
		author='Vlamo/Dimitrij',
		author_email='dima-73@inbox.lv',
		package_dir={'Extensions.VCS': 'src'},
		packages=['Extensions.VCS'],
		package_data={'Extensions.VCS': ['*.png', '*.sh']},
		description='video clipping switcher',
		cmdclass=setup_translate.cmdclass,
	)
