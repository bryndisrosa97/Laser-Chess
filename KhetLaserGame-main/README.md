# 02180_Introduction_to_Artificial_Intelligence
Board Game project

# To lauch the game
Launch the `laser_view.py` file. It can be done in an editor or in a terminal with the command:
```
cd <path/to/laserChess>
python laser_view.py
```

# For developers
run `pre-commit install` after you cloned the repository so that the files are reformatted when you commit.

Here is an example of how to use git to make changes - we don't need to follow that closely, the main point is to pull the master before making a new branch and **make a branch before making changes**.
- Open an issue explaining the features/ changes/ fixes.
- Make sure your master branch is updated (`git pull origin master`).
- Switch to a new branch (`git checkout -b <branch_name>`). An example of good branche name would be `issue/<issue_number>/<keyword>`.
- Add and commit your changes/ files: `git commit -a`, `git add`/ `git rm` to add/delete files
- Push your branch to gitHub (`git push origin <branch-name>`).
- Create a merge request from your branch.
- Make any suggested changes based on the code review, then push those changes.
- After the merge request is accepted, pull the new changes to master (git checkout master, then git pull origin master).
