# SeaweedFS File Storage Implementation

import asyncio
import aiohttp
import os
from typing import Optional

from app.domain.interfaces import FileStorage
from app.core.config import settings
from app.core.logger import logger


class SeaweedFSFileStorage(FileStorage):
    """SeaweedFS implementation of FileStorage"""
    
    def __init__(
        self,
        master_url: str = settings.SEAWEEDFS_MASTER_URL,
        volume_url: str = settings.SEAWEEDFS_VOLUME_URL
    ):
        self.master_url = master_url
        self.volume_url = volume_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def upload(self, file_path: str, destination: str = None) -> str:
        """Upload file to SeaweedFS and return file ID"""
        try:
            # Step 1: Request a fid from master
            session = await self._get_session()
            
            logger.info(f"Connecting to SeaweedFS Master at: {self.master_url}/dir/assign")
            async with session.get(f"{self.master_url}/dir/assign") as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to get fid from SeaweedFS: {resp.status}")
                
                data = await resp.json()
                fid = data.get("fid")
                file_url = data.get("url")
            
            logger.info(f"Got fid from SeaweedFS: {fid}")
            
            # Step 2: Upload file to volume server
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                
                async with session.post(
                    f"http://{file_url}/{fid}",
                    data=files
                ) as resp:
                    if resp.status not in [200, 201]:
                        raise Exception(f"Failed to upload file: {resp.status}")
                    
                    upload_data = await resp.json()
                    logger.info(f"File uploaded to SeaweedFS: {fid}")
                    
                    return fid
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            raise
    
    async def download(self, file_id: str, destination: str) -> bool:
        """Download file from SeaweedFS"""
        try:
            session = await self._get_session()
            
            # Parse file_id to get volume and needle
            # Format: 3,01235e09c3c3f14
            parts = file_id.split(',')
            if len(parts) != 2:
                raise ValueError(f"Invalid file_id format: {file_id}")
            
            volume_id, needle_id = parts
            
            # Get volume server location from master
            async with session.get(f"{self.master_url}/dir/lookup?volumeId={volume_id}") as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to lookup volume: {resp.status}")
                
                data = await resp.json()
                if not data.get("locations"):
                    raise Exception(f"No volume locations found for {volume_id}")
                
                location = data["locations"][0]
                file_url = f"http://{location['url']}/{file_id}"
            
            # Download file
            async with session.get(file_url) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to download file: {resp.status}")
                
                # Ensure destination directory exists
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                
                with open(destination, 'wb') as f:
                    f.write(await resp.read())
            
            logger.info(f"File downloaded from SeaweedFS: {file_id} -> {destination}")
            return True
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            raise
    
    async def delete(self, file_id: str) -> bool:
        """Delete file from SeaweedFS"""
        try:
            session = await self._get_session()
            
            # Parse file_id
            parts = file_id.split(',')
            if len(parts) != 2:
                raise ValueError(f"Invalid file_id format: {file_id}")
            
            volume_id, needle_id = parts
            
            # Get volume server location
            async with session.get(f"{self.master_url}/dir/lookup?volumeId={volume_id}") as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to lookup volume: {resp.status}")
                
                data = await resp.json()
                if not data.get("locations"):
                    raise Exception(f"No volume locations found for {volume_id}")
                
                location = data["locations"][0]
                file_url = f"http://{location['url']}/{file_id}"
            
            # Delete file
            async with session.delete(file_url) as resp:
                if resp.status not in [200, 202, 404]:
                    raise Exception(f"Failed to delete file: {resp.status}")
            
            logger.info(f"File deleted from SeaweedFS: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            raise
    
    async def exists(self, file_id: str) -> bool:
        """Check if file exists in SeaweedFS"""
        try:
            session = await self._get_session()
            
            # Parse file_id
            parts = file_id.split(',')
            if len(parts) != 2:
                return False
            
            volume_id, needle_id = parts
            
            # Get volume server location
            async with session.get(f"{self.master_url}/dir/lookup?volumeId={volume_id}") as resp:
                if resp.status != 200:
                    return False
                
                data = await resp.json()
                if not data.get("locations"):
                    return False
                
                location = data["locations"][0]
                file_url = f"http://{location['url']}/{file_id}"
            
            # Check file existence with HEAD request
            async with session.head(file_url) as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Error checking file existence {file_id}: {e}")
            return False
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
