#include "layoutstoolmain.h"
#include "utils.h"
#include <QDebug>

LayoutsToolMain::LayoutsToolMain(QObject *parent) :
        QObject(parent) {

    // Find layouts.h path (check for Mixxx directory four directories up)
    bool layoutsFound = false;
    QDir cp = QDir::currentPath();

    for (int i = 0; i < 5; i++) {
        QString path(cp.absolutePath()+"/src/controllers/keyboard/layouts.cpp");
        QFileInfo checkFile(path);

        if (checkFile.exists() && checkFile.isFile()) {
            mFilePath = path;
            qDebug() << "Found path: " << path;
            layoutsFound = true;
        }
        cp.cdUp();
    }

    if (!layoutsFound) {
        mFilePath = "";
    }

    app = qApp;
    pLayoutsFileHandler = new LayoutsFileHandler();
}

void LayoutsToolMain::run() {
    qDebug() << "Welcome to the Layouts tool :)";

    pLayoutsFileHandler->open(mFilePath, mLayouts);
    mainMenu();

    // Get display from X
    m_xDisplay = QX11Info::display();
}

void LayoutsToolMain::quit() {
    emit finished();
}

void LayoutsToolMain::aboutToQuitApp() {
    delete pLayoutsFileHandler;
}

void LayoutsToolMain::mainMenu() {
    QTextStream qtin(stdin);

    bool userWantsToQuit = false;
    do {
        bool loaded = !mFilePath.isEmpty();
        int menuChoice = 0;

        // Print menu
        utils::clearTerminal();
        qDebug() << "********** LAYOUTS TOOL - MAIN MENU **********";
        if (loaded) qDebug() << "Currently opened file: " << mFilePath;
        qDebug() << "(1): Open file";
        qDebug() << "(2): Save file";
        if (loaded) qDebug() << "(3): Edit file";
        qDebug() << (loaded ? "(4): Quit" : "(3): Quit");

        // Prompt user for choice
        qtin >> menuChoice;

        switch(menuChoice) {
            case 1: {
                utils::clearTerminal();
                qDebug() << "Please tell me the path to the layouts cpp file (no spaces please): ";
                qtin >> mFilePath;
                pLayoutsFileHandler->open(mFilePath, mLayouts);
                break;
            }

            case 2: {
                qDebug() << "Save file...";
                QFile f(mFilePath);
                pLayoutsFileHandler->save(f, mLayouts);
                break;
            }

            case 3: {
                if (loaded) {
                    editLayoutMenu();
                } else {
                    qDebug() << "Exit...";
                    quit();
                }
                break;
            }

            case 4: {
                if (loaded) {
                    userWantsToQuit = true;
                    quit();
                }
                break;
            }

            default:
                qDebug() << "ERROR! You have selected an invalid choice.";
                break;
        }
    } while (!userWantsToQuit);
}

void LayoutsToolMain::editLayoutMenu() {
    QTextStream qtin(stdin);
    bool loaded = !mFilePath.isEmpty();
    if (!loaded) {
        qDebug() << "Can't edit any layout, any layout loaded.";
        return;
    }

    bool backToMain = false;
    do {
        int menuChoice = 0;

        // Print menu
        utils::clearTerminal();
        qDebug() << "********** LAYOUTS TOOL - EDIT **********";
        qDebug() << "Editing file: " << mFilePath;
        qDebug() << "(1): Remove layout";
        qDebug() << "(2): Add layout";
        qDebug() << "(3): Back to main menu";

        // Prompt user for choice
        qtin >> menuChoice;

        switch(menuChoice) {
            case 1: {
                // Remove layouts
                qDebug() << "Remove layouts...";
                removeLayoutMenu();
                break;
            }

            case 2: {
                // Add layout
                qDebug() << "Add layout...";
                addLayoutMenu();
                break;
            }

            case 3: {
                // Back to main menu
                backToMain = true;
                break;
            }

            default:
                qDebug() << "ERROR! You have selected an invalid choice.";
                break;
        }
    } while (!backToMain);
}

void LayoutsToolMain::addLayoutMenu() {
    QTextStream qtin(stdin);
    QString kbdLocale = utils::inputLocaleName();

    utils::clearTerminal();
    qDebug() << "********** LAYOUTS TOOL - ADD LAYOUT **********";
    qDebug() << "Qt keyboard locale: " << kbdLocale
             << " (NOTE: This is not accurate any more when changing layout runtime)";

    qDebug() << "Enter layout name: ";
    QString layoutName = kbdLocale;
    qtin.skipWhiteSpace();
    layoutName = qtin.readLine();

    qDebug() << "Enter layout variable name (see Qt keyboard locale): ";
    QString varName = kbdLocale;
    qtin >> varName;

    qDebug() << QString("\nAdding layout with:\n  Name:\t\t\t\t%1\n  Variable name:\t%2\n").arg(layoutName, varName)
            .toStdString()
            .c_str();

    Layout layout(layoutName, varName);
    mLayouts.append(layout);
}

void LayoutsToolMain::removeLayoutMenu() {
    QTextStream qtin(stdin);

    bool backToEdit;
    do {
        int menuChoice = 0;

        // Print menu
        utils::clearTerminal();
        qDebug() << "********** LAYOUTS TOOL - REMOVE LAYOUT **********";
        showLayouts();
        qDebug("(%d)  %s", mLayouts.size(), "Back to edit menu");

        // Prompt user for choice
        qtin >> menuChoice;

        if (menuChoice == mLayouts.size()) {
            break;
        }

        if (menuChoice >= mLayouts.size() || menuChoice < 0) {
            qDebug() << "ERROR! You have selected an invalid choice.";
            continue;
        }

        mLayouts.removeAt(menuChoice);
        backToEdit = true;
    } while (!backToEdit);
}

void LayoutsToolMain::showLayouts() {
    int i = 0;
    for (Layout &layout : mLayouts) {
        qDebug("(%d)  %s, [%s]", i++, layout.name.toLatin1().data(), layout.varName.toLatin1().data());
    }
}