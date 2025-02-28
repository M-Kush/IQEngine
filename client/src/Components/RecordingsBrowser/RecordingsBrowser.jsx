// Copyright (c) 2022 Microsoft Corporation
// Copyright (c) 2023 Marc Lichtman
// Licensed under the MIT License

import React, { useEffect, useState } from 'react';
import Directory from './Directory';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { useLocation, useSearchParams } from 'react-router-dom';
import {
  updateConnectionAccountName,
  updateConnectionContainerName,
  updateConnectionSasToken,
} from '@/Store/Reducers/ConnectionReducer';

import { resetBlobObject } from '@/Store/Reducers/BlobReducer';

import { fetchRecordingsList } from '@/Store/Reducers/RecordingsListReducer';
import { useAppDispatch, useAppSelector } from '@/Store/hooks';

function isFolder(file) {
  return file.name.endsWith('/');
}

function GroupByFolder(files, root) {
  const fileTree = {
    contents: [],
    children: [],
  };

  files.map((file) => {
    const relativeKey = file.name.substr(root.length);
    let currentFolder = fileTree;
    const folders = relativeKey.split('/');
    folders.forEach((folder, folderIndex) => {
      if (folderIndex === folders.length - 1 && isFolder(file)) {
        for (const key in file) {
          currentFolder[key] = file[key];
        }
      }
      if (folder === '') {
        return;
      }
      const isAFile = !isFolder(file) && folderIndex === folders.length - 1;
      if (isAFile) {
        currentFolder.contents.push({
          ...file,
          relativeKey: relativeKey,
          keyDerived: true,
          type: 'file',
          name: file.name.replaceAll('/', '(slash)'), // because we cant use slashes in the url, we undo this replace before grabbing the blob, as well as displaying it in the table
        });
      } else {
        if (folder in currentFolder.children === false) {
          currentFolder.children[folder] = {
            contents: [],
            children: [],
            type: 'folder',
          };
        }
        currentFolder = currentFolder.children[folder];
      }
    });
    return {
      ...file,
      relativeKey: relativeKey,
    };
  });

  function addAllChildren(level, prefix) {
    if (prefix !== '') {
      prefix += '/';
    }
    let files = [];
    for (const folder in level.children) {
      //console.log('children');
      //console.log(folder);
      files.push({
        ...level.children[folder],
        contents: undefined,
        keyDerived: true,
        name: folder,
        relativeKey: prefix + folder + '/',
        children: addAllChildren(level.children[folder], prefix + folder),
      });
    }
    files = files.concat(level.contents);
    return files;
  }

  files = addAllChildren(fileTree, '');
  return files;
}

export default function RecordingsBrowser() {
  const connection = useAppSelector((state) => state.connection);
  const recording = useAppSelector((state) => state.recordingsList);
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const dispatch = useAppDispatch();

  const data = recording.recordingsList;

  const [currentFolder, setCurrentFolder] = useState('root');
  const [load, toggleLoader] = useState(true);

  // Load in the connection info based on repoId
  useEffect(() => {
    // This will happen when someone is linked directly to an azure repo
    if (location.search && !connection.accountName) {
      console.log('Updating connection info and fetching recordings list!');
      const accountName = searchParams.get('accountName');
      const containerName = searchParams.get('containerName');
      const sasToken = searchParams.get('sasToken');
      dispatch(updateConnectionAccountName(accountName));
      dispatch(updateConnectionContainerName(containerName));
      dispatch(updateConnectionSasToken(sasToken));
    }
    dispatch(resetBlobObject());
  }, []);

  useEffect(() => {
    // This will happen when someone is linked directly to an azure repo
    if (connection && connection.accountName && connection.containerName && connection.sasToken) {
      dispatch(fetchRecordingsList(connection));
    }
  }, [connection]);

  useEffect(() => {
    toggleLoader(recording.loading);
  }, [recording.loading]);

  const gfiles = data.map((data) => data.name);
  let dataTree = [];
  let currentDataTree = [];

  if (gfiles.length > 0) {
    dataTree = GroupByFolder(data, '');
    dataTree = { children: dataTree, name: 'root', type: 'folder' };
    // find the portion corresponding to current folder
    function findCurrentFolder(x) {
      // 1 layer deep (TODO: Make recursive)
      if (x.name === currentFolder) {
        x.parentName = 'root';
        return x;
      }
      // 2 layers deep
      for (const child of x.children) {
        if (child.type === 'folder') {
          if (child.name === currentFolder) {
            child.parentName = x.name;
            return child;
          }
        }
      }
      // 3 layers deep
      for (const child of x.children) {
        if (child.type === 'folder') {
          for (const c of child.children) {
            if (c.name === currentFolder) {
              c.parentName = child.name;
              return c;
            }
          }
        }
      }
    }
    currentDataTree = findCurrentFolder(dataTree);

    // remove all children from folders in currentDataTree so they dont show up
    for (let i = 0; i < currentDataTree.children.length; i++) {
      if (currentDataTree.children[i].type === 'folder') {
        currentDataTree.children[i].children = [];
      }
    }
  }

  return (
    <div className="container-fluid">
      {load ? (
        <center>
          <svg
            className="animate-spin ml-1 mr-3 h-2/5 w-2/5 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1"></circle>
            <circle className="percent fifty stroke-current text-primary" cx="12" cy="12" r="10" pathLength="100" />
          </svg>
        </center>
      ) : (
        <table className="table w-full">
          <thead>
            <tr style={{ textAlign: 'center' }}>
              <th>Spectrogram Thumbnail</th>
              <th style={{ minWidth: '10%' }}>Recording Name</th>
              <th>Length in Samples</th>
              <th>
                Data Type{' '}
                <a
                  style={{ textDecoration: 'none', color: 'white', margin: '5px 0 0 5px' }}
                  target="_blank"
                  rel="noreferrer"
                  href="https://pysdr.org/content/iq_files.html#binary-files"
                >
                  <InfoOutlinedIcon></InfoOutlinedIcon>
                </a>
              </th>
              <th>Frequency</th>
              <th>Sample Rate</th>
              <th>Number of Annotations</th>
              <th style={{ width: '10%' }}>Author</th>
            </tr>
          </thead>
          <tbody>
            <Directory
              key={Math.random()}
              item={currentDataTree}
              setCurrentFolder={setCurrentFolder}
              currentFolder={currentFolder}
            />
          </tbody>
        </table>
      )}
    </div>
  );
}
